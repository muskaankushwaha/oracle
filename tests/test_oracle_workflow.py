"""Tests for the LangGraph investigation workflow."""

from oracle_api import workflow


def make_scan(findings):
    return {
        "repository": {"name": "example/project", "branch": "main", "url": "https://github.com/example/project"},
        "analyzedAt": "2026-11-01T00:00:00+00:00",
        "scan": {"filesFound": len(findings), "filesScanned": len(findings), "fileLimit": 35, "byteLimitPerFile": 80000, "scannedBytes": 100, "truncated": False, "failedFiles": 0, "method": "test"},
        "files": [finding["file"] for finding in findings],
        "findings": findings,
        "disclaimer": "Review findings.",
    }


def test_workflow_ranks_issue_related_evidence_and_preserves_confidence(monkeypatch):
    findings = [
        {"id": "a", "title": "TLS verification disabled", "file": "src/network.py", "line": 9, "severity": "high", "confidence": 0.9, "category": "Security risk", "evidence": "verify=False", "suggestion": "Enable verification."},
        {"id": "b", "title": "Bare exception handler", "file": "src/checkout.py", "line": 22, "severity": "low", "confidence": 0.7, "category": "Potential bug", "evidence": "except:", "suggestion": "Catch a specific exception."},
    ]
    monkeypatch.setattr(workflow, "analyze_repository", lambda *_: make_scan(findings))

    result = workflow.run_investigation("example", "project", "secret", "checkout fails after deployment", lambda *_: {})

    assert result["investigation"]["engine"] == "LangGraph"
    assert result["investigation"]["usesExternalModel"] is False
    checkout = next(item for item in result["hypotheses"] if item["file"] == "src/checkout.py")
    assert checkout["confidence"] == 0.7
    assert checkout["matchedTerms"] == ["checkout"]
    assert checkout["bayesian"]["posterior"] > checkout["bayesian"]["prior"]
    assert checkout["riskAssessment"]["method"] == "Mamdani fuzzy inference"
    assert "incident-term overlap" in checkout["reason"]
    assert result["riskAssessment"]["score"] >= checkout["riskAssessment"]["score"]
    assert "genetic algorithm" in result["investigation"]["rankingMethod"]


def test_workflow_reports_empty_candidate_list(monkeypatch):
    monkeypatch.setattr(workflow, "analyze_repository", lambda *_: make_scan([]))

    result = workflow.run_investigation("example", "project", "secret", "checkout returns 500", lambda *_: {})

    assert result["hypotheses"] == []
    assert "No checked source patterns matched" in result["investigation"]["summary"]
    assert result["riskAssessment"] is None
    assert result["testPlan"]["tests"] == []
    assert result["logAnalysis"]["classifications"] == []


def test_workflow_classifies_logs_and_prioritizes_test_files(monkeypatch):
    findings = [
        {"id": "checkout", "title": "Bare exception handler", "file": "src/checkout.py", "line": 22, "severity": "high", "confidence": 0.8, "category": "Potential bug", "evidence": "except:", "suggestion": "Catch a specific exception."},
    ]
    scan = make_scan(findings)
    scan["testCandidates"] = [
        {"id": "tests/test_checkout.py", "covers": ["src/checkout.py"], "duration_s": 1, "durationSource": "assumed"},
        {"id": "tests/test_profile.py", "covers": ["src/profile.py"], "duration_s": 1, "durationSource": "assumed"},
    ]
    monkeypatch.setattr(workflow, "analyze_repository", lambda *_: scan)

    result = workflow.run_investigation(
        "example", "project", "secret", "checkout fails", lambda *_: {},
        "ERROR sqlite database transaction failed",
    )

    assert result["logAnalysis"]["classifications"][0]["category"] == "database"
    assert result["testPlan"]["engine"] == "Genetic algorithm"
    assert result["testPlan"]["tests"][0]["id"] == "tests/test_checkout.py"
    assert "not execute" in result["testPlan"]["note"]
