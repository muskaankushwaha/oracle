"""Privacy-conscious evaluation utilities for ORACLE's soft-computing models.

Submission source for ``oracle/softcomputing/evaluation_metrics.py``. Functions
operate on labels and numeric predictions only; they never log training text.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class EvaluationReport:
    rows: int
    labels: tuple[str, ...]
    accuracy: float
    majority_baseline: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    confusion: dict[str, dict[str, int]]
    warnings: tuple[str, ...] = ()

    def as_dict(self) -> dict:
        return {
            "rows": self.rows, "labels": list(self.labels), "accuracy": self.accuracy,
            "majorityBaseline": self.majority_baseline, "macroPrecision": self.macro_precision,
            "macroRecall": self.macro_recall, "macroF1": self.macro_f1,
            "confusionMatrix": self.confusion, "warnings": list(self.warnings),
        }


# Progress 01/20 — Validate labels and discard empty labels without exposing text.
def normalize_labels(values: Iterable[object]) -> list[str]:
    output: list[str] = []
    for value in values:
        if isinstance(value, str) and value.strip():
            output.append(value.strip().lower())
    return output


# Progress 02/20 — Count labels in stable order.
def label_counts(labels: Sequence[str]) -> dict[str, int]:
    return dict(sorted(Counter(labels).items()))


# Progress 03/20 — Check minimum examples per class before cross-validation.
def minimum_class_count(labels: Sequence[str]) -> int:
    counts = label_counts(labels)
    return min(counts.values(), default=0)


# Progress 04/20 — Select a feasible stratified fold count.
def feasible_folds(labels: Sequence[str], requested: int = 5, maximum: int = 10) -> int:
    available = minimum_class_count(labels)
    if available < 2:
        return 0
    return max(2, min(int(requested), int(maximum), available))


# Progress 05/20 — Validate paired predictions before calculating metrics.
def validate_pairs(actual: Sequence[str], predicted: Sequence[str]) -> tuple[list[str], list[str]]:
    if len(actual) != len(predicted):
        raise ValueError("Actual and predicted label counts must match.")
    if not actual:
        raise ValueError("At least one labeled example is required.")
    return list(actual), list(predicted)


# Progress 06/20 — Build a complete confusion matrix, including zero cells.
def confusion_matrix(actual: Sequence[str], predicted: Sequence[str]) -> dict[str, dict[str, int]]:
    actual, predicted = validate_pairs(actual, predicted)
    labels = sorted(set(actual) | set(predicted))
    matrix = {truth: {guess: 0 for guess in labels} for truth in labels}
    for truth, guess in zip(actual, predicted):
        matrix[truth][guess] += 1
    return matrix


# Progress 07/20 — Calculate accuracy with explicit empty-input behavior.
def accuracy(actual: Sequence[str], predicted: Sequence[str]) -> float:
    actual, predicted = validate_pairs(actual, predicted)
    return sum(truth == guess for truth, guess in zip(actual, predicted)) / len(actual)


# Progress 08/20 — Calculate a majority-class baseline on the same labels.
def majority_baseline(actual: Sequence[str]) -> float:
    if not actual:
        raise ValueError("At least one labeled example is required.")
    return max(Counter(actual).values()) / len(actual)


# Progress 09/20 — Compute per-class precision safely.
def class_precision(matrix: dict[str, dict[str, int]], label: str) -> float:
    predicted_total = sum(row.get(label, 0) for row in matrix.values())
    true_positive = matrix.get(label, {}).get(label, 0)
    return true_positive / predicted_total if predicted_total else 0.0


# Progress 10/20 — Compute per-class recall safely.
def class_recall(matrix: dict[str, dict[str, int]], label: str) -> float:
    row = matrix.get(label, {})
    support = sum(row.values())
    return row.get(label, 0) / support if support else 0.0


# Progress 11/20 — Compute per-class F1 with zero-division handling.
def class_f1(matrix: dict[str, dict[str, int]], label: str) -> float:
    precision = class_precision(matrix, label)
    recall = class_recall(matrix, label)
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


# Progress 12/20 — Average a metric equally across classes.
def macro_average(matrix: dict[str, dict[str, int]], metric) -> float:
    labels = list(matrix)
    return sum(metric(matrix, label) for label in labels) / len(labels) if labels else 0.0


# Progress 13/20 — Add multiclass macro F1, precision and recall.
def macro_metrics(matrix: dict[str, dict[str, int]]) -> dict[str, float]:
    return {
        "precision": macro_average(matrix, class_precision),
        "recall": macro_average(matrix, class_recall),
        "f1": macro_average(matrix, class_f1),
    }


# Progress 14/20 — Reject invalid probability values in calibration reports.
def valid_probability(value: object) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and 0.0 <= value <= 1.0


# Progress 15/20 — Calculate a bounded expected calibration error.
def expected_calibration_error(confidences: Sequence[float], correct: Sequence[bool], bins: int = 10) -> float:
    if len(confidences) != len(correct) or not confidences:
        raise ValueError("Confidence and correctness lists must be non-empty and equal length.")
    if not all(valid_probability(value) for value in confidences):
        raise ValueError("Confidence values must be finite probabilities between zero and one.")
    bin_count = max(2, min(int(bins), 100))
    total = len(confidences)
    error = 0.0
    for index in range(bin_count):
        lower, upper = index / bin_count, (index + 1) / bin_count
        members = [(score, hit) for score, hit in zip(confidences, correct)
                   if lower <= score < upper or (index == bin_count - 1 and score == 1.0)]
        if members:
            mean_confidence = sum(score for score, _ in members) / len(members)
            mean_accuracy = sum(bool(hit) for _, hit in members) / len(members)
            error += len(members) / total * abs(mean_confidence - mean_accuracy)
    return error


# Progress 16/20 — Detect severe label imbalance for report warnings.
def imbalance_ratio(labels: Sequence[str]) -> float:
    counts = label_counts(labels)
    if not counts or min(counts.values()) == 0:
        return math.inf
    return max(counts.values()) / min(counts.values())


# Progress 17/20 — Generate warnings without printing source log examples.
def evaluation_warnings(labels: Sequence[str], folds: int) -> tuple[str, ...]:
    warnings: list[str] = []
    if len(set(labels)) < 2:
        warnings.append("At least two label classes are required for classification evaluation.")
    if minimum_class_count(labels) < folds:
        warnings.append("The smallest class cannot support the requested stratified fold count.")
    if imbalance_ratio(labels) > 10:
        warnings.append("Labels are highly imbalanced; interpret accuracy alongside macro F1.")
    return tuple(warnings)


# Progress 18/20 — Assemble one reproducible report from held-out predictions.
def evaluate_predictions(actual: Sequence[str], predicted: Sequence[str]) -> EvaluationReport:
    actual, predicted = validate_pairs(actual, predicted)
    matrix = confusion_matrix(actual, predicted)
    scores = macro_metrics(matrix)
    labels = tuple(sorted(set(actual) | set(predicted)))
    return EvaluationReport(
        rows=len(actual), labels=labels, accuracy=accuracy(actual, predicted),
        majority_baseline=majority_baseline(actual), macro_precision=scores["precision"],
        macro_recall=scores["recall"], macro_f1=scores["f1"], confusion=matrix,
        warnings=evaluation_warnings(actual, feasible_folds(actual)),
    )


# Progress 19/20 — Keep metric serialization finite and JSON-safe.
def json_safe_number(value: float) -> float | None:
    return round(value, 6) if math.isfinite(value) else None


# Progress 20/20 — Export the evaluation API for scripts and tests.
__all__ = [
    "EvaluationReport", "accuracy", "class_f1", "class_precision", "class_recall",
    "confusion_matrix", "evaluation_warnings", "evaluate_predictions",
    "expected_calibration_error", "feasible_folds", "imbalance_ratio", "label_counts",
    "majority_baseline", "macro_metrics", "normalize_labels", "valid_probability",
]
