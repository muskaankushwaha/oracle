"""Best-effort MLP log classification trained on bundled synthetic examples.

This is a wiring/demo model, not a production classifier. It is not trained on
the user's repository or logs, and its output scores are not calibrated.
"""

from __future__ import annotations

import csv
from collections import Counter
from functools import lru_cache
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline


TRAINING_EXAMPLES: dict[str, tuple[str, ...]] = {
    "validation": (
        "ValidationError email field failed validation",
        "invalid input value schema required field missing",
        "request body failed pydantic validation for user name",
        "ValueError invalid field format for postal code",
        "form submission rejected because required field is empty",
        "input does not match expected validation pattern",
        "serializer rejected invalid choice for status field",
        "payload validation error unexpected field supplied",
    ),
    "database": (
        "sqlite database is locked while executing query",
        "psycopg database connection refused by postgres server",
        "SQL transaction failed and rollback was issued",
        "database query raised integrity constraint violation",
        "mysql operational error lost connection during commit",
        "deadlock detected while waiting for database transaction",
        "could not connect to database host after retry",
        "SQLAlchemy session failed to execute select statement",
    ),
    "external_api": (
        "HTTP request to upstream API timed out",
        "external service returned HTTP 503 unavailable",
        "requests connection error calling payment API",
        "remote server response status 502 bad gateway",
        "third party API rate limit exceeded after retry",
        "HTTP client failed TLS connection to external endpoint",
        "upstream request returned 504 gateway timeout",
        "webhook delivery failed with remote API error",
    ),
    "config": (
        "configuration error missing DATABASE_URL environment variable",
        "required setting API_HOST is not configured",
        "invalid config value for server port",
        "environment variable SECRET_KEY is unset",
        "could not load application configuration file",
        "configuration parser found malformed setting",
        "missing credentials in deployment config",
        "unsupported value in runtime settings file",
    ),
    "null_value": (
        "AttributeError NoneType object has no attribute name",
        "TypeError cannot read property from undefined value",
        "null reference encountered while accessing user profile",
        "object is None and has no attribute identifier",
        "undefined value dereference in request handler",
        "NoneType object is not subscriptable",
        "cannot call method on null response object",
        "missing value caused null pointer exception",
    ),
    "arithmetic": (
        "ZeroDivisionError division by zero in invoice calculation",
        "OverflowError numeric result too large for conversion",
        "arithmetic error while computing average value",
        "cannot divide integer by zero in billing total",
        "numeric overflow when calculating account balance",
        "invalid numeric operand in rate calculation",
        "floating point underflow during price computation",
        "math domain error while computing square root",
    ),
    "logic": (
        "AssertionError expected state completed but found pending",
        "invariant failed after order state transition",
        "unexpected branch reached in payment workflow",
        "logic error result should be nonempty after processing",
        "assertion failed expected one item but received zero",
        "impossible state encountered in state machine",
        "condition mismatch while validating workflow result",
        "unexpected result violates application invariant",
    ),
    "other": (
        "RuntimeError operation failed unexpectedly",
        "unhandled exception occurred in background worker",
        "process terminated after an unknown failure",
        "unexpected traceback from application task",
        "worker crashed with an unspecified runtime failure",
        "unknown exception while handling application request",
        "operation aborted due to an unclassified error",
        "fatal error occurred during service startup",
    ),
}

ERROR_CUES: dict[str, tuple[str, ...]] = {
    "validation": ("validation", "invalid", "required", "schema", "field", "payload", "serializer"),
    "database": ("database", "sql", "query", "sqlite", "postgres", "transaction", "deadlock", "session"),
    "external_api": ("http", "upstream", "api", "request", "remote", "webhook", "gateway", "timeout"),
    "config": ("config", "configuration", "environment", "setting", "credentials", "unset"),
    "null_value": ("none", "null", "undefined", "nonetype", "attribute", "reference", "dereference"),
    "arithmetic": ("division", "divide", "zero", "overflow", "arithmetic", "numeric", "calculation", "math"),
    "logic": ("assertion", "invariant", "state", "branch", "condition", "unexpected", "logic"),
    "other": ("runtimeerror", "unhandled", "unknown", "unclassified", "fatal", "worker"),
}

MAX_LOG_LINES = 100
MAX_LINE_LENGTH = 1200
MAX_TRAINING_ROWS = 50_000
MAX_DATASET_BYTES = 10_000_000
MIN_EXAMPLES_PER_CATEGORY = 5
DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "labeled_logs.csv"


def _build_model():
    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        token_pattern=r"(?u)\b[a-zA-Z_][a-zA-Z0-9_]*\b",
        sublinear_tf=True,
    )
    classifier = MLPClassifier(
        hidden_layer_sizes=(24,),
        activation="relu",
        solver="lbfgs",
        alpha=0.01,
        max_iter=500,
        random_state=42,
    )
    return make_pipeline(vectorizer, classifier)


@lru_cache(maxsize=2)
def _model(texts: tuple[str, ...], labels: tuple[str, ...]):
    pipeline = _build_model()
    pipeline.fit(list(texts), list(labels))
    return pipeline


def load_labeled_log_dataset(path: str | Path | None = None) -> list[dict[str, str]]:
    """Load validated `message,category` rows from a local CSV file."""
    dataset_path = Path(path) if path is not None else DATASET_PATH
    if not dataset_path.is_file():
        raise FileNotFoundError(f"Labeled log dataset not found: {dataset_path}")
    if dataset_path.stat().st_size > MAX_DATASET_BYTES:
        raise ValueError(f"Labeled log dataset exceeds {MAX_DATASET_BYTES} bytes.")

    rows = []
    with dataset_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not {"message", "category"}.issubset(reader.fieldnames or []):
            raise ValueError("CSV must have message and category columns.")
        for row_number, row in enumerate(reader, start=2):
            if len(rows) >= MAX_TRAINING_ROWS:
                raise ValueError(f"Dataset exceeds {MAX_TRAINING_ROWS} rows.")
            message = (row.get("message") or "").strip()
            category = (row.get("category") or "").strip().lower()
            if not message or len(message) > 2000:
                raise ValueError(f"Row {row_number} needs a message of 1-2,000 characters.")
            if category not in ERROR_CUES:
                raise ValueError(
                    f"Row {row_number} has unknown category {category!r}; "
                    f"use one of {', '.join(sorted(ERROR_CUES))}."
                )
            rows.append({"message": message, "category": category})
    if not rows:
        raise ValueError("Dataset has no labeled examples.")
    return rows


def _training_data() -> tuple[tuple[str, ...], tuple[str, ...], str, str]:
    try:
        rows = load_labeled_log_dataset()
        counts = Counter(row["category"] for row in rows)
        if len(counts) < 2 or min(counts.values()) < MIN_EXAMPLES_PER_CATEGORY:
            raise ValueError(
                f"Add at least {MIN_EXAMPLES_PER_CATEGORY} examples for each of at least "
                "two categories before using the local dataset for MLP training."
            )
        return (
            tuple(row["message"] for row in rows),
            tuple(row["category"] for row in rows),
            "local labeled CSV",
            f"Trained on {len(rows)} local labeled rows. Scores are uncalibrated; validate them with the evaluation script.",
        )
    except (FileNotFoundError, OSError, ValueError) as error:
        texts = tuple(text for examples in TRAINING_EXAMPLES.values() for text in examples)
        labels = tuple(label for label, examples in TRAINING_EXAMPLES.items() for _ in examples)
        if isinstance(error, FileNotFoundError):
            note = "No local labeled CSV was found; using bundled synthetic demo examples. Scores are uncalibrated."
        else:
            note = f"Local labeled CSV was not used ({error}); using bundled synthetic demo examples. Scores are uncalibrated."
        return texts, labels, "bundled synthetic examples", note


def evaluate_labeled_log_dataset(path: str | Path | None = None) -> dict:
    """Return stratified cross-validation metrics for a manually labeled CSV."""
    rows = load_labeled_log_dataset(path)
    texts = [row["message"] for row in rows]
    labels = [row["category"] for row in rows]
    counts = Counter(labels)
    if len(counts) < 2 or min(counts.values()) < 2:
        raise ValueError("Evaluation needs at least two categories and two examples per category.")
    folds = min(5, min(counts.values()))
    predicted = cross_val_predict(
        _build_model(), texts, labels,
        cv=StratifiedKFold(n_splits=folds, shuffle=True, random_state=42),
    )
    report = classification_report(
        labels, predicted, output_dict=True, zero_division=0
    )
    majority_category = counts.most_common(1)[0][0]
    majority_baseline = [majority_category] * len(labels)
    return {
        "examples": len(rows),
        "folds": folds,
        "accuracy": round(float(accuracy_score(labels, predicted)), 4),
        "macroF1": round(float(f1_score(labels, predicted, average="macro", zero_division=0)), 4),
        "majorityBaselineAccuracy": round(float(accuracy_score(labels, majority_baseline)), 4),
        "perCategory": {
            category: {
                "precision": round(report[category]["precision"], 4),
                "recall": round(report[category]["recall"], 4),
                "f1": round(report[category]["f1-score"], 4),
                "support": int(report[category]["support"]),
            }
            for category in sorted(counts)
        },
        "note": "Cross-validation metrics estimate performance on this labeled sample; they are not a production guarantee.",
    }


def classify_log_text(log_text: str) -> dict:
    """Classify nonblank log lines and include lexical cues for review."""
    lines = [
        (number, line.strip()[:MAX_LINE_LENGTH])
        for number, line in enumerate(str(log_text).splitlines(), start=1)
        if line.strip()
    ]
    selected = lines[:MAX_LOG_LINES]
    if not selected:
        return {
            "classifications": [],
            "model": "scikit-learn MLP with one hidden layer",
            "trainingExamples": 0,
            "trainingSource": "not used; no logs supplied",
            "truncated": False,
            "note": "Paste representative logs to request best-effort category predictions.",
        }

    training_texts, training_labels, training_source, training_note = _training_data()
    model = _model(training_texts, training_labels)
    probabilities = model.predict_proba([line for _, line in selected])
    predicted = model.classes_[probabilities.argmax(axis=1)]
    results = []
    for index, ((line_number, line), category) in enumerate(zip(selected, predicted)):
        normalized = line.lower()
        cues = [cue for cue in ERROR_CUES[str(category)] if cue in normalized]
        results.append({
            "line": line_number,
            "message": line,
            "category": str(category),
            "modelScore": round(float(probabilities[index].max()), 4),
            "matchedCues": cues,
            "explanation": (
                f"The bundled MLP selected {category}; matched lexical cues: "
                f"{', '.join(cues) if cues else 'none'}; verify this label against the full incident context."
            ),
        })

    note = f"{training_note} Predictions are suggestions and need human review."
    if len(lines) > MAX_LOG_LINES:
        note += f" Only the first {MAX_LOG_LINES} nonblank lines were classified."
    return {
        "classifications": results,
        "model": "scikit-learn MLP with one hidden layer",
        "trainingExamples": len(training_texts),
        "trainingSource": training_source,
        "truncated": len(lines) > MAX_LOG_LINES,
        "note": note,
    }
