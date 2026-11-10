"""Unit tests for ORACLE's explainable soft-computing modules."""

import pytest

from oracle.softcomputing.bayes_hypothesis import update_hypothesis_probability
from oracle.softcomputing.fuzzy_risk import assess_fuzzy_risk
from oracle.softcomputing.ga_test_priority import prioritize_tests
from oracle.softcomputing.log_classifier import classify_log_text
from oracle.softcomputing.log_classifier import evaluate_labeled_log_dataset, load_labeled_log_dataset


def test_bayesian_update_is_neutral_without_issue_evidence():
    result = update_hypothesis_probability(0.7, 0, 0)

    assert result["prior"] == pytest.approx(0.7)
    assert result["likelihoodRatio"] == 1.0
    assert result["posterior"] == pytest.approx(0.7)
    assert "not been calibrated" in result["calibrationNote"]


def test_bayesian_update_increases_when_issue_terms_match():
    result = update_hypothesis_probability(0.5, 2, 4)

    assert result["likelihoodRatio"] == 3.0
    assert result["posterior"] == pytest.approx(0.75)
    assert "2/4" in result["reason"]


def test_fuzzy_risk_returns_explainable_score_and_orders_low_below_high():
    low = assess_fuzzy_risk("low", 0.25, 0.2)
    high = assess_fuzzy_risk("critical", 0.95, 0.95)

    assert 0 <= low["score"] <= 100
    assert high["score"] > low["score"]
    assert high["level"] == "high"
    assert high["method"] == "Mamdani fuzzy inference"
    assert set(high["ruleActivations"]) == {"low", "medium", "high"}


def test_mlp_classifies_log_lines_and_discloses_synthetic_training():
    result = classify_log_text("\nERROR sqlite database transaction failed")

    assert result["classifications"][0]["category"] == "database"
    assert result["classifications"][0]["line"] == 2
    assert "database" in result["classifications"][0]["matchedCues"]
    assert result["trainingSource"] == "bundled synthetic examples"
    assert "uncalibrated" in result["note"]


def test_genetic_algorithm_prioritizes_risk_linked_test_and_is_repeatable():
    tests = [
        {"id": "tests/test_profile.py", "covers": ["src/profile.py"], "duration_s": 1},
        {"id": "tests/test_checkout.py", "covers": ["src/checkout.py"], "duration_s": 1},
    ]
    hypotheses = [{
        "file": "src/checkout.py",
        "priorityScore": 0.8,
        "riskAssessment": {"score": 85},
    }]

    first = prioritize_tests(tests, hypotheses, seed=7)
    second = prioritize_tests(tests, hypotheses, seed=7)

    assert first == second
    assert first["tests"][0]["id"] == "tests/test_checkout.py"
    assert first["tests"][0]["withinBudget"] is True
    assert "did not execute" in first["note"]


def test_genetic_algorithm_handles_no_test_candidates():
    result = prioritize_tests([], [])

    assert result["tests"] == []
    assert "No candidate test files" in result["objective"]


def test_genetic_algorithm_returns_each_candidate_once_under_a_time_budget():
    tests = [
        {"id": f"tests/test_{index}.py", "covers": [], "duration_s": 2}
        for index in range(8)
    ]

    result = prioritize_tests(tests, [], budget_seconds=3, seed=9)

    assert len(result["tests"]) == len(tests)
    assert len({item["id"] for item in result["tests"]}) == len(tests)
    assert sum(item["withinBudget"] for item in result["tests"]) == 1


def test_local_labeled_csv_can_train_and_be_cross_validated(tmp_path, monkeypatch):
    dataset = tmp_path / "labeled_logs.csv"
    database = [
        "sqlite database connection failed",
        "SQL transaction rollback error",
        "postgres database query timed out",
        "database session could not commit",
        "SQL query failed on database server",
    ]
    config = [
        "missing configuration environment variable",
        "config setting is not configured",
        "invalid config file setting",
        "environment variable is unset",
        "configuration parser error in settings",
    ]
    rows = [f'"{message}",database' for message in database]
    rows += [f'"{message}",config' for message in config]
    dataset.write_text("message,category\n" + "\n".join(rows) + "\n", encoding="utf-8")
    monkeypatch.setattr("oracle.softcomputing.log_classifier.DATASET_PATH", dataset)

    loaded = load_labeled_log_dataset()
    metrics = evaluate_labeled_log_dataset()
    classified = classify_log_text("ERROR sqlite database connection failed")

    assert len(loaded) == 10
    assert metrics["folds"] == 5
    assert 0 <= metrics["accuracy"] <= 1
    assert 0 <= metrics["majorityBaselineAccuracy"] <= 1
    assert set(metrics["perCategory"]) == {"config", "database"}
    assert classified["trainingSource"] == "local labeled CSV"
