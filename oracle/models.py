"""Shared data models for ORACLE.

This file is the contract between all four modules. Every function in tools/,
softcomputing/, the pipeline and the dashboard takes and returns these classes,
so the pieces fit together at the end.

Rules for changing this file:
  * Only Muskan merges changes here, and every change is announced to the team.
  * Add new fields with a default value, so nobody else's code breaks.
  * Never rename or delete a field without updating every caller in the same PR.

Owner: Muskan Kushwaha
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _new_id(prefix: str) -> str:
    """Short readable id such as 'hyp-3f9a1c'."""
    return f"{prefix}-{uuid4().hex[:6]}"


def _now() -> datetime:
    return datetime.now(timezone.utc)


class OracleModel(BaseModel):
    """Base class: reject unknown fields (catches typos) and re-check values on assignment."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True)


# --------------------------------------------------------------------------- #
# Enums: the fixed vocabularies everyone shares
# --------------------------------------------------------------------------- #


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Labels the neural network predicts for a log line, and the kind of a hypothesis."""

    VALIDATION = "validation"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    CONFIG = "config"
    NULL_VALUE = "null_value"
    ARITHMETIC = "arithmetic"
    LOGIC = "logic"
    OTHER = "other"


class EvidenceKind(str, Enum):
    LOG = "log"
    COMMIT = "commit"
    DIFF = "diff"
    CODE = "code"
    TEST = "test"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    SKIPPED = "skipped"   # the module behind this step is not built yet
    FAILED = "failed"


class HypothesisStatus(str, Enum):
    OPEN = "open"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"


# --------------------------------------------------------------------------- #
# Inputs: the bug report and raw material ORACLE collects
# --------------------------------------------------------------------------- #


class Issue(OracleModel):
    """The bug report ORACLE is asked to investigate."""

    id: str = Field(default_factory=lambda: _new_id("issue"))
    title: str = Field(min_length=1)
    description: str = ""
    error_message: Optional[str] = None      # e.g. "500 Internal Server Error"
    stack_trace: Optional[str] = None
    reported_at: datetime = Field(default_factory=_now)
    severity: Severity = Severity.MEDIUM
    users_affected: int = Field(default=0, ge=0)   # an input to the fuzzy risk system


class CodeLocation(OracleModel):
    """A place in the code: a file, optionally a line and function."""

    file: str                               # path relative to the repo root
    line: Optional[int] = Field(default=None, ge=1)
    function: Optional[str] = None
    snippet: Optional[str] = None

    def __str__(self) -> str:
        return f"{self.file}:{self.line}" if self.line else self.file


class Commit(OracleModel):
    """One Git commit, as returned by tools/git_tools.py."""

    sha: str = Field(min_length=7)
    author: str
    date: datetime
    message: str
    files_changed: list[str] = Field(default_factory=list)
    lines_added: int = Field(default=0, ge=0)
    lines_deleted: int = Field(default=0, ge=0)

    @property
    def short_sha(self) -> str:
        return self.sha[:7]

    @property
    def lines_changed(self) -> int:
        return self.lines_added + self.lines_deleted

    def age_days(self, now: Optional[datetime] = None) -> float:
        """Days between this commit and `now`. An input to the fuzzy risk system."""
        now = now or _now()
        date = self.date if self.date.tzinfo else self.date.replace(tzinfo=timezone.utc)
        return max(0.0, (now - date).total_seconds() / 86_400)


class LogEntry(OracleModel):
    """One parsed log line, as returned by tools/log_tools.py."""

    message: str
    level: str = "INFO"                      # INFO, WARNING, ERROR, ...
    timestamp: Optional[datetime] = None
    source: Optional[str] = None             # logger name or file
    raw: str = ""                            # the original line, untouched
    # Filled in by the neural network (softcomputing/log_classifier.py):
    category: Optional[ErrorCategory] = None
    category_confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    @field_validator("level")
    @classmethod
    def _upper_level(cls, v: str) -> str:
        return v.upper()

    @property
    def is_error(self) -> bool:
        return self.level in {"ERROR", "CRITICAL", "FATAL"}


class TestCase(OracleModel):
    """A test that can be run, and which files it covers. Input to the GA."""

    __test__ = False                         # stops pytest trying to collect this class

    id: str                                  # pytest node id, e.g. "tests/test_pay.py::test_inr"
    covers: list[str] = Field(default_factory=list)   # source files this test exercises
    duration_s: float = Field(default=1.0, gt=0.0)


class TestResult(OracleModel):
    __test__ = False

    test_id: str
    passed: bool
    duration_s: float = Field(default=0.0, ge=0.0)
    output: str = ""


# --------------------------------------------------------------------------- #
# Reasoning: evidence, hypotheses, risk, fix plan
# --------------------------------------------------------------------------- #


class Evidence(OracleModel):
    """One piece of evidence found during the investigation.

    `likelihoods` maps a hypothesis id to P(E | H): how likely we would be to see
    this evidence if that hypothesis were true. The Bayesian engine reads these.
    A hypothesis missing from the dict is treated as neutral (no update).
    """

    id: str = Field(default_factory=lambda: _new_id("ev"))
    kind: EvidenceKind
    summary: str                             # one line a human can read
    source: str = ""                         # file path, commit sha or log file name
    location: Optional[CodeLocation] = None
    category: Optional[ErrorCategory] = None
    likelihoods: dict[str, float] = Field(default_factory=dict)
    found_at: datetime = Field(default_factory=_now)

    @field_validator("likelihoods")
    @classmethod
    def _likelihoods_are_probabilities(cls, v: dict[str, float]) -> dict[str, float]:
        for hyp_id, p in v.items():
            if not 0.0 <= p <= 1.0:
                raise ValueError(f"P(E|H) for {hyp_id} must be between 0 and 1, got {p}")
        return v


class Hypothesis(OracleModel):
    """A possible root cause, with ORACLE's current belief in it."""

    id: str = Field(default_factory=lambda: _new_id("hyp"))
    title: str                               # e.g. "Invalid currency value"
    description: str = ""
    category: ErrorCategory = ErrorCategory.OTHER
    suspect_files: list[str] = Field(default_factory=list)
    suspect_commit: Optional[str] = None     # sha
    prior: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)   # current posterior
    confidence_history: list[float] = Field(default_factory=list)  # for the Timeline tab
    evidence_ids: list[str] = Field(default_factory=list)
    status: HypothesisStatus = HypothesisStatus.OPEN

    def set_confidence(self, value: float) -> None:
        """Update the posterior and remember the old value for the dashboard timeline."""
        self.confidence_history.append(self.confidence)
        self.confidence = value


class RiskAssessment(OracleModel):
    """Output of the fuzzy inference system."""

    score: float = Field(ge=0.0, le=100.0)
    level: RiskLevel
    inputs: dict[str, float] = Field(default_factory=dict)   # crisp inputs, for explaining
    explanation: str = ""                                     # which rules fired


class FixPlan(OracleModel):
    """What to change, and which tests to run in which order."""

    summary: str
    steps: list[str] = Field(default_factory=list)
    files_to_change: list[str] = Field(default_factory=list)
    test_order: list[str] = Field(default_factory=list)      # TestCase ids, from the GA
    approved: bool = False


class StepRecord(OracleModel):
    """One entry in the audit trail: what a pipeline step did."""

    number: int = Field(ge=1, le=8)
    name: str
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    message: str = ""

    @property
    def duration_s(self) -> Optional[float]:
        if self.started_at and self.finished_at:
            return (self.finished_at - self.started_at).total_seconds()
        return None


# --------------------------------------------------------------------------- #
# The investigation: the one object every pipeline step reads and adds to
# --------------------------------------------------------------------------- #


class Investigation(OracleModel):
    id: str = Field(default_factory=lambda: _new_id("inv"))
    issue: Issue
    repo_path: str
    log_paths: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)

    # Step 1 Understand
    keywords: list[str] = Field(default_factory=list)
    mentioned_files: list[str] = Field(default_factory=list)
    # Step 2 Explore
    code_hits: list[CodeLocation] = Field(default_factory=list)
    dependencies: dict[str, list[str]] = Field(default_factory=dict)   # file -> files it imports
    # Step 3 Investigate
    commits: list[Commit] = Field(default_factory=list)
    logs: list[LogEntry] = Field(default_factory=list)
    # Steps 4-6 Hypothesize, Verify, Diagnose
    evidence: list[Evidence] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    # Step 7 Impact
    risk: Optional[RiskAssessment] = None
    impacted_files: list[str] = Field(default_factory=list)
    # Step 8 Fix plan
    tests: list[TestCase] = Field(default_factory=list)
    fix_plan: Optional[FixPlan] = None
    test_results: list[TestResult] = Field(default_factory=list)

    summary: str = ""
    steps: list[StepRecord] = Field(default_factory=list)   # the audit trail

    # ---- helpers ---------------------------------------------------------- #

    def add_evidence(self, ev: Evidence) -> Evidence:
        self.evidence.append(ev)
        return ev

    def get_hypothesis(self, hyp_id: str) -> Hypothesis:
        for h in self.hypotheses:
            if h.id == hyp_id:
                return h
        raise KeyError(f"No hypothesis with id {hyp_id!r}")

    def ranked_hypotheses(self) -> list[Hypothesis]:
        """Hypotheses, most likely first."""
        return sorted(self.hypotheses, key=lambda h: h.confidence, reverse=True)

    @property
    def top_hypothesis(self) -> Optional[Hypothesis]:
        ranked = self.ranked_hypotheses()
        return ranked[0] if ranked else None

    @property
    def error_logs(self) -> list[LogEntry]:
        return [entry for entry in self.logs if entry.is_error]

    def step(self, number: int) -> StepRecord:
        for s in self.steps:
            if s.number == number:
                return s
        raise KeyError(f"No step {number}")
