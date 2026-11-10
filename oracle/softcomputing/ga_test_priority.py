"""Genetic algorithm that orders discovered test files by likely early value."""

from __future__ import annotations

import random
from math import sqrt


POPULATION_SIZE = 40
GENERATIONS = 60
DEFAULT_BUDGET_SECONDS = 300.0


def _fitness(order: list[int], tests: list[dict], risk_weights: dict[str, float], budget: float) -> float:
    elapsed = 0.0
    covered: set[str] = set()
    score = 0.0
    has_suspects = bool(risk_weights)
    for index in order:
        test = tests[index]
        duration = max(0.1, float(test.get("duration_s", 1.0)))
        if elapsed + duration > budget:
            break
        test_covers = set(test.get("covers", []))
        if has_suspects:
            newly_covered = test_covers - covered
            benefit = sum(risk_weights.get(path, 0.0) for path in newly_covered)
        else:
            # With no source findings, favor fast tests as a smoke-test order.
            benefit = 1.0
        score += benefit / sqrt(1.0 + elapsed)
        covered.update(test_covers)
        elapsed += duration
    return score


def _order_crossover(first: list[int], second: list[int], rng: random.Random) -> list[int]:
    size = len(first)
    if size < 2:
        return first[:]
    left, right = sorted(rng.sample(range(size), 2))
    child: list[int | None] = [None] * size
    child[left:right + 1] = first[left:right + 1]
    remaining = [gene for gene in second if gene not in child]
    slots = list(range(right + 1, size)) + list(range(0, right + 1))
    for slot, gene in zip(slots, remaining):
        child[slot] = gene
    return [int(gene) for gene in child]


def _mutate(order: list[int], rng: random.Random, rate: float = 0.2) -> None:
    if len(order) > 1 and rng.random() < rate:
        first, second = rng.sample(range(len(order)), 2)
        order[first], order[second] = order[second], order[first]


def _risk_weights(hypotheses: list[dict]) -> dict[str, float]:
    weights: dict[str, float] = {}
    for hypothesis in hypotheses:
        file_path = hypothesis.get("file")
        if not file_path:
            continue
        risk = hypothesis.get("riskAssessment", {}).get("score")
        if risk is None:
            risk = 100.0 * float(hypothesis.get("priorityScore", 0.0))
        weights[file_path] = max(weights.get(file_path, 0.0), max(0.0, float(risk)) / 100.0)
    return weights


def prioritize_tests(
    candidates: list[dict], hypotheses: list[dict], *,
    budget_seconds: float = DEFAULT_BUDGET_SECONDS, seed: int = 42,
) -> dict:
    """Find a useful early test order without running any repository tests."""
    tests = [item for item in candidates if item.get("id")]
    if not tests:
        return {
            "tests": [],
            "engine": "Genetic algorithm",
            "timeBudgetSeconds": budget_seconds,
            "objective": "No candidate test files were found in the repository tree.",
            "durationBasis": "unavailable",
            "note": "ORACLE did not execute repository code.",
        }

    rng = random.Random(seed)
    weights = _risk_weights(hypotheses)
    size = len(tests)
    population = [list(range(size))]
    population.extend(rng.sample(range(size), size) for _ in range(POPULATION_SIZE - 1))

    def evaluate(order: list[int]) -> float:
        return _fitness(order, tests, weights, max(0.1, budget_seconds))

    for _ in range(GENERATIONS):
        population.sort(key=evaluate, reverse=True)
        next_population = [item[:] for item in population[:2]]
        while len(next_population) < POPULATION_SIZE:
            first = max(rng.sample(population[:12], min(4, len(population[:12]))), key=evaluate)
            second = max(rng.sample(population[:12], min(4, len(population[:12]))), key=evaluate)
            child = _order_crossover(first, second, rng)
            _mutate(child, rng)
            next_population.append(child)
        population = next_population

    best = max(population, key=evaluate)
    elapsed = 0.0
    covered: set[str] = set()
    ordered = []
    for rank, index in enumerate(best, start=1):
        test = tests[index]
        duration = max(0.1, float(test.get("duration_s", 1.0)))
        test_covers = set(test.get("covers", []))
        newly_covered = sorted(test_covers - covered)
        inside_budget = elapsed + duration <= budget_seconds
        ordered.append({
            "rank": rank,
            "id": test["id"],
            "covers": sorted(test_covers),
            "newRiskFilesCovered": newly_covered,
            "estimatedDurationSeconds": round(duration, 2),
            "durationSource": test.get("durationSource", "estimated; no run history available"),
            "coverageSource": test.get("coverageSource", "inferred from file names"),
            "withinBudget": inside_budget,
            "reason": (
                f"Covers {len(newly_covered)} newly prioritized source file(s) in the first-pass order."
                if newly_covered else "Adds a quick regression check after the higher-impact coverage."
            ),
        })
        covered.update(test_covers)
        elapsed += duration

    return {
        "tests": ordered,
        "engine": "Genetic algorithm",
        "generations": GENERATIONS,
        "populationSize": POPULATION_SIZE,
        "fitnessScore": round(evaluate(best), 4),
        "timeBudgetSeconds": budget_seconds,
        "estimatedSuiteSeconds": round(elapsed, 2),
        "objective": (
            "Maximize risk-weighted coverage of files linked to findings early in the order, "
            "within the time budget. With no findings, prefer faster smoke tests."
        ),
        "durationBasis": (
            "recorded CI timings for all test files"
            if all("measured" in test.get("durationSource", "") for test in tests)
            else "mixed recorded timings and assumptions"
            if any("measured" in test.get("durationSource", "") for test in tests)
            else "assumed estimates; test run history is not connected"
        ),
        "coverageBasis": (
            "reported CI coverage is available for some tests"
            if any("reported CI coverage" in test.get("coverageSource", "") for test in tests)
            else "source coverage inferred from test and source file names"
        ),
        "note": "Suggested order only. ORACLE did not execute repository code or tests.",
    }
