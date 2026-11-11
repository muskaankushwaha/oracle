"""Small, explainable Bayesian update for source-based bug hypotheses.

The static rule confidence values are not calibrated probabilities. This module
uses them as prior proxies and reports that limitation with every result.
"""

from __future__ import annotations


CALIBRATION_NOTE = (
    "Estimate only: source-rule confidence is hand-set and has not been calibrated "
    "against a labelled dataset."
)


def update_hypothesis_probability(
    prior_proxy: float, matched_term_count: int, issue_term_count: int
) -> dict:
    """Update a rule-confidence prior proxy with issue-term overlap evidence."""
    prior = min(0.99, max(0.01, float(prior_proxy)))
    matched = max(0, int(matched_term_count))
    total = max(0, int(issue_term_count))
    overlap = min(1.0, matched / total) if total else 0.0

    # Overlap contributes a modest likelihood ratio: 1 with no issue evidence,
    # rising to 5 when all issue terms also occur in the source finding.
    likelihood_ratio = 1.0 + (4.0 * overlap) if total else 1.0
    prior_odds = prior / (1.0 - prior)
    posterior_odds = prior_odds * likelihood_ratio
    posterior = posterior_odds / (1.0 + posterior_odds)

    if total:
        reason = (
            f"Bayes update: prior proxy {prior:.0%}; incident-term overlap "
            f"{matched}/{total} ({overlap:.0%}) gives likelihood ratio "
            f"{likelihood_ratio:.2f}; posterior estimate {posterior:.0%}."
        )
    else:
        reason = (
            f"No issue description was supplied, so no symptom evidence updated "
            f"the prior proxy {prior:.0%}; posterior estimate {posterior:.0%}."
        )

    return {
        "prior": round(prior, 4),
        "likelihoodRatio": round(likelihood_ratio, 4),
        "posterior": round(posterior, 4),
        "matchedTermCount": matched,
        "incidentTermCount": total,
        "overlap": round(overlap, 4),
        "method": "Bayes odds update using issue-term overlap",
        "reason": reason,
        "calibrationNote": CALIBRATION_NOTE,
    }
