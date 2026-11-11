"""Mamdani fuzzy risk inference with inspectable input and rule activations."""

from __future__ import annotations

import numpy as np
import skfuzzy as fuzz


SEVERITY_INPUT = {"low": 20.0, "medium": 50.0, "high": 78.0, "critical": 96.0}
UNIVERSE = np.arange(0.0, 101.0, 1.0)


def _memberships(value: float) -> dict[str, float]:
    value = float(np.clip(value, 0.0, 100.0))
    return {
        "low": float(fuzz.interp_membership(UNIVERSE, fuzz.trapmf(UNIVERSE, [0, 0, 25, 55]), value)),
        "medium": float(fuzz.interp_membership(UNIVERSE, fuzz.trimf(UNIVERSE, [25, 50, 75]), value)),
        "high": float(fuzz.interp_membership(UNIVERSE, fuzz.trapmf(UNIVERSE, [55, 75, 100, 100]), value)),
    }


def assess_fuzzy_risk(severity: str, detector_confidence: float, posterior: float) -> dict:
    """Infer a 0-100 risk score and return the Mamdani rule activations."""
    severity_key = str(severity).lower()
    severity_value = SEVERITY_INPUT.get(severity_key, SEVERITY_INPUT["low"])
    confidence_value = float(np.clip(detector_confidence, 0.0, 1.0)) * 100.0
    posterior_value = float(np.clip(posterior, 0.0, 1.0)) * 100.0

    impact = _memberships(severity_value)
    confidence = _memberships(confidence_value)
    probability = _memberships(posterior_value)

    low_activation = min(impact["low"], confidence["low"], probability["low"])
    medium_activation = max(
        min(impact["medium"], confidence["medium"]),
        min(impact["high"], confidence["low"]),
        min(impact["medium"], probability["medium"]),
        min(confidence["high"], probability["medium"]),
    )
    high_activation = max(
        min(impact["high"], confidence["high"]),
        probability["high"],
        min(impact["high"], probability["medium"]),
        min(confidence["high"], probability["medium"]),
    )

    low_output = fuzz.trapmf(UNIVERSE, [0, 0, 25, 50])
    medium_output = fuzz.trimf(UNIVERSE, [25, 50, 75])
    high_output = fuzz.trapmf(UNIVERSE, [50, 75, 100, 100])
    aggregate = np.fmax(
        np.fmax(np.fmin(low_activation, low_output), np.fmin(medium_activation, medium_output)),
        np.fmin(high_activation, high_output),
    )
    if not np.any(aggregate):
        score = 0.0
    else:
        score = float(fuzz.defuzz(UNIVERSE, aggregate, "centroid"))

    level = "low" if score < 35 else "medium" if score < 65 else "high"
    return {
        "score": round(score, 1),
        "level": level,
        "method": "Mamdani fuzzy inference",
        "inputs": {
            "severity": severity_key,
            "severityValue": severity_value,
            "detectorConfidence": round(confidence_value, 1),
            "bayesianPosterior": round(posterior_value, 1),
        },
        "ruleActivations": {
            "low": round(low_activation, 3),
            "medium": round(medium_activation, 3),
            "high": round(high_activation, 3),
        },
        "explanation": (
            f"Mamdani rules combine {severity_key} severity (impact {severity_value:.0f}/100), "
            f"detector confidence ({confidence_value:.0f}/100), and Bayesian posterior "
            f"({posterior_value:.0f}/100) into a {level} risk score."
        ),
    }
