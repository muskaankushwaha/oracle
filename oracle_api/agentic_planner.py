"""Bounded, evidence-first planning helpers for ORACLE's LangGraph.

Submission source for ``oracle_api/agentic_planner.py``. The planner is
deterministic: it routes among existing read-only tools and does not send
repository source to an external model or write to GitHub.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any, Literal, TypedDict

ToolName = Literal[
    "scan_source", "classify_logs", "rank_evidence", "prioritize_tests",
    "verify_evidence", "publish_report",
]
MAX_GRAPH_STEPS = 8
MAX_FOLLOW_UPS = 1
MAX_TRACE_ITEMS = 32


class PlannerState(TypedDict, total=False):
    issue_report: str
    log_text: str
    scan_result: dict[str, Any]
    log_analysis: dict[str, Any]
    hypotheses: list[dict[str, Any]]
    test_plan: dict[str, Any]
    completed_actions: list[str]
    follow_up_count: int
    step_count: int
    trace: list[dict[str, Any]]
    stop_reason: str


@dataclass(frozen=True)
class PlannerDecision:
    """One constrained decision made by the deterministic planner."""

    next_action: ToolName
    reason: str
    stop: bool = False


@dataclass
class InvestigationBudget:
    """Hard limits for graph work; does not execute any repository code."""

    max_steps: int = MAX_GRAPH_STEPS
    max_follow_ups: int = MAX_FOLLOW_UPS
    timeout_seconds: float = 45.0
    started_at: float = field(default_factory=time.monotonic)
    steps_used: int = 0
    follow_ups_used: int = 0

    def can_step(self) -> bool:
        return self.steps_used < max(1, self.max_steps) and self.elapsed < self.timeout_seconds

    @property
    def elapsed(self) -> float:
        return max(0.0, time.monotonic() - self.started_at)

    def consume_step(self) -> bool:
        if not self.can_step():
            return False
        self.steps_used += 1
        return True

    def consume_follow_up(self) -> bool:
        if self.follow_ups_used >= max(0, self.max_follow_ups) or not self.can_step():
            return False
        self.follow_ups_used += 1
        return True


# Progress 01/20 — Define the allowlist of tools the planner may route to.
ALLOWED_ACTIONS: frozenset[str] = frozenset({
    "scan_source", "classify_logs", "rank_evidence", "prioritize_tests",
    "verify_evidence", "publish_report",
})


# Progress 02/20 — Normalize optional user text without retaining arbitrary objects.
def clean_text(value: object, limit: int = 20_000) -> str:
    if not isinstance(value, str):
        return ""
    return value.replace("\x00", "")[: max(0, limit)]


# Progress 03/20 — Select log classification only when user supplied logs.
def should_classify_logs(state: PlannerState) -> bool:
    return bool(clean_text(state.get("log_text", "")).strip())


# Progress 04/20 — Detect whether scan output contains test candidates.
def has_test_candidates(state: PlannerState) -> bool:
    candidates = state.get("scan_result", {}).get("testCandidates", [])
    return isinstance(candidates, list) and bool(candidates)


# Progress 05/20 — Produce a visible, reproducible action plan.
def plan_actions(state: PlannerState) -> list[ToolName]:
    actions: list[ToolName] = ["scan_source"]
    if should_classify_logs(state):
        actions.append("classify_logs")
    actions.append("rank_evidence")
    if has_test_candidates(state):
        actions.append("prioritize_tests")
    actions.extend(["verify_evidence", "publish_report"])
    return actions[:MAX_GRAPH_STEPS]


# Progress 06/20 — Validate requested action names before routing.
def safe_action(value: object) -> ToolName | None:
    if isinstance(value, str) and value in ALLOWED_ACTIONS:
        return value  # type: ignore[return-value]
    return None


# Progress 07/20 — Read completed graph actions from trusted state only.
def completed_actions(state: PlannerState) -> set[str]:
    values = state.get("completed_actions", [])
    if not isinstance(values, list):
        return set()
    return {item for item in values if isinstance(item, str) and item in ALLOWED_ACTIONS}


# Progress 08/20 — Choose the first planned action that has not completed.
def next_planned_action(state: PlannerState) -> PlannerDecision:
    done = completed_actions(state)
    for action in plan_actions(state):
        if action not in done:
            return PlannerDecision(action, f"{action} is required by the current input and scan state.")
    return PlannerDecision("publish_report", "All selected read-only analysis steps are complete.")


# Progress 09/20 — Permit only one evidence follow-up when evidence is absent.
def should_follow_up(state: PlannerState, budget: InvestigationBudget) -> bool:
    if budget.follow_ups_used >= budget.max_follow_ups:
        return False
    findings = state.get("scan_result", {}).get("findings", [])
    has_logs = should_classify_logs(state)
    return not findings and has_logs and budget.can_step()


# Progress 10/20 — Add follow-up only when the bounded planner allows it.
def choose_follow_up(state: PlannerState, budget: InvestigationBudget) -> PlannerDecision:
    if should_follow_up(state, budget) and budget.consume_follow_up():
        return PlannerDecision("classify_logs", "No source findings were found; classify supplied logs once for additional context.")
    return PlannerDecision("verify_evidence", "No further evidence-gathering pass is allowed.")


# Progress 11/20 — Normalize repository path separators for evidence checks.
def normalize_path(value: object) -> str:
    path = str(value or "").replace("\\", "/").strip("/")
    parts = [part for part in path.split("/") if part not in ("", ".")]
    if any(part == ".." for part in parts):
        return ""
    return "/".join(parts)


# Progress 12/20 — Parse a bounded evidence line number.
def line_number(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if 1 <= number <= 10_000_000 else None


# Progress 13/20 — Verify a finding against the exact scanned source line.
def verify_source_finding(finding: dict[str, Any], source_lines: dict[str, list[str]]) -> dict[str, Any]:
    path = normalize_path(finding.get("file"))
    line = line_number(finding.get("line"))
    lines = source_lines.get(path, []) if path else []
    valid_location = line is not None and line <= len(lines)
    actual = lines[line - 1].strip() if valid_location else ""
    reported = str(finding.get("evidence", "")).strip()
    verified = bool(actual and reported and (reported in actual or actual in reported))
    return {**finding, "evidenceVerified": verified, "evidenceStatus": "verified" if verified else "unverified"}


# Progress 14/20 — Verify all candidates without upgrading them to confirmed causes.
def verify_findings(findings: object, source_lines: dict[str, list[str]]) -> list[dict[str, Any]]:
    if not isinstance(findings, list):
        return []
    return [verify_source_finding(item, source_lines) for item in findings if isinstance(item, dict)]


# Progress 15/20 — Cap trace size and keep only planner metadata.
def append_trace(state: PlannerState, action: str, reason: str, status: str) -> list[dict[str, str]]:
    trace = state.get("trace", [])
    safe = [item for item in trace if isinstance(item, dict)] if isinstance(trace, list) else []
    safe.append({"action": action[:40], "reason": reason[:240], "status": status[:40]})
    return safe[-MAX_TRACE_ITEMS:]


# Progress 16/20 — Stop on explicit step or wall-clock budgets.
def budget_stop_reason(budget: InvestigationBudget) -> str | None:
    if budget.steps_used >= budget.max_steps:
        return "step_budget_reached"
    if budget.elapsed >= budget.timeout_seconds:
        return "time_budget_reached"
    return None


# Progress 17/20 — Explain tool failures without including raw exceptions.
def tool_failure(reason: object) -> dict[str, str]:
    safe = str(reason or "tool_error")[:80]
    return {"status": "failed", "reason": safe}


# Progress 18/20 — Build transparent report metadata from the plan.
def plan_summary(state: PlannerState) -> dict[str, Any]:
    return {
        "engine": "LangGraph",
        "mode": "bounded_deterministic_router",
        "plannedActions": plan_actions(state),
        "usesExternalModel": False,
        "repositoryWritesAllowed": False,
    }


# Progress 19/20 — Keep a clear stop message when evidence is insufficient.
def evidence_disclaimer(verified: int, total: int) -> str:
    if total == 0:
        return "No candidate evidence was found; this does not prove the reported issue has no cause."
    if verified < total:
        return "Some candidate evidence could not be verified against the scanned source; review it manually."
    return "Evidence references matched scanned source lines; candidates still require engineer review."


# Progress 20/20 — Export the stable integration surface for workflow.py.
__all__ = [
    "InvestigationBudget", "PlannerDecision", "PlannerState", "append_trace",
    "budget_stop_reason", "choose_follow_up", "evidence_disclaimer", "next_planned_action",
    "plan_actions", "plan_summary", "safe_action", "verify_findings", "verify_source_finding",
]
