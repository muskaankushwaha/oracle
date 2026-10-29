"""Tests for oracle/models.py: the shared data classes.

Run with:  pytest tests/test_models.py -v
"""

from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from oracle.models import (
    Commit,
    ErrorCategory,
    Evidence,
    EvidenceKind,
    Hypothesis,
    Investigation,
    Issue,
    LogEntry,
    RiskAssessment,
    RiskLevel,
    StepRecord,
    StepStatus,
)


def make_investigation() -> Investigation:
    """A small investigation like the PDF example, reused by several tests."""
    return Investigation(
        issue=Issue(title="Checkout returns 500", error_message="Invalid currency: INR"),
        repo_path="workspace/eshop",
    )


# --- Issue ------------------------------------------------------------------ #

def test_issue_gets_an_id_and_defaults():
    issue = Issue(title="Checkout returns 500")
    assert issue.id.startswith("issue-")
    assert issue.users_affected == 0
    assert issue.severity.value == "medium"


def test_issue_title_cannot_be_empty():
    with pytest.raises(ValidationError):
        Issue(title="")


def test_unknown_field_is_rejected():
    # A typo like "titel" must fail loudly instead of being silently ignored.
    with pytest.raises(ValidationError):
        Issue(title="Bug", titel="typo")


# --- Commit ----------------------------------------------------------------- #

def test_commit_helpers():
    now = datetime(2026, 11, 3, tzinfo=timezone.utc)
    commit = Commit(
        sha="a1b2c3d4e5f6",
        author="Iman",
        date=now - timedelta(days=1),
        message="Change currency validation",
        lines_added=10,
        lines_deleted=4,
    )
    assert commit.short_sha == "a1b2c3d"
    assert commit.lines_changed == 14
    assert commit.age_days(now) == pytest.approx(1.0)


# --- LogEntry --------------------------------------------------------------- #

def test_log_level_is_uppercased_and_error_detected():
    entry = LogEntry(message="Invalid currency: INR", level="error")
    assert entry.level == "ERROR"
    assert entry.is_error


def test_log_category_confidence_must_be_a_probability():
    with pytest.raises(ValidationError):
        LogEntry(message="x", category=ErrorCategory.VALIDATION, category_confidence=1.5)


# --- Evidence and Hypothesis ------------------------------------------------ #

def test_evidence_likelihoods_must_be_between_0_and_1():
    with pytest.raises(ValidationError):
        Evidence(kind=EvidenceKind.LOG, summary="bad", likelihoods={"hyp-1": 2.0})


def test_set_confidence_keeps_history_for_the_timeline():
    hyp = Hypothesis(title="Invalid currency value", confidence=0.5)
    hyp.set_confidence(0.74)
    hyp.set_confidence(0.91)
    assert hyp.confidence == 0.91
    assert hyp.confidence_history == [0.5, 0.74]


def test_confidence_cannot_go_above_1():
    hyp = Hypothesis(title="Database issue")
    with pytest.raises(ValidationError):
        hyp.confidence = 1.2      # validate_assignment catches this


# --- Investigation ---------------------------------------------------------- #

def test_ranked_and_top_hypothesis():
    inv = make_investigation()
    assert inv.top_hypothesis is None
    inv.hypotheses = [
        Hypothesis(title="Database issue", confidence=0.10),
        Hypothesis(title="Invalid currency value", confidence=0.91),
        Hypothesis(title="Payment gateway timeout", confidence=0.32),
    ]
    assert [h.title for h in inv.ranked_hypotheses()] == [
        "Invalid currency value",
        "Payment gateway timeout",
        "Database issue",
    ]
    assert inv.top_hypothesis.title == "Invalid currency value"


def test_get_hypothesis_by_id():
    inv = make_investigation()
    hyp = Hypothesis(title="Invalid currency value")
    inv.hypotheses.append(hyp)
    assert inv.get_hypothesis(hyp.id) is hyp
    with pytest.raises(KeyError):
        inv.get_hypothesis("hyp-missing")


def test_error_logs_filters_by_level():
    inv = make_investigation()
    inv.logs = [
        LogEntry(message="Order placed", level="INFO"),
        LogEntry(message="Invalid currency: INR", level="ERROR"),
    ]
    assert [e.message for e in inv.error_logs] == ["Invalid currency: INR"]


def test_step_record_duration():
    start = datetime(2026, 11, 3, 10, 0, 0, tzinfo=timezone.utc)
    step = StepRecord(number=1, name="Understand", status=StepStatus.DONE,
                      started_at=start, finished_at=start + timedelta(seconds=2))
    assert step.duration_s == 2.0


def test_investigation_survives_a_json_round_trip():
    # The SQLite storage saves investigations as JSON, so this must work.
    inv = make_investigation()
    inv.hypotheses.append(Hypothesis(title="Invalid currency value", confidence=0.91))
    inv.risk = RiskAssessment(score=82, level=RiskLevel.HIGH)

    copy = Investigation.model_validate_json(inv.model_dump_json())

    assert copy == inv
    assert copy.risk.level is RiskLevel.HIGH
