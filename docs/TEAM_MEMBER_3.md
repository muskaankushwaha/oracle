# Teammate 3 — Soft computing and data validation plan

**Ownership:** Bayesian hypothesis updates, fuzzy risk scoring, MLP log classification, genetic test ordering and honest model evaluation. Replace this heading with the contributor’s name and GitHub handle.

## Existing code in this area

- `oracle/softcomputing/bayes_hypothesis.py` — explainable odds update using hand-set detector confidence proxies.
- `oracle/softcomputing/fuzzy_risk.py` — Mamdani fuzzy risk score.
- `oracle/softcomputing/log_classifier.py` — MLP log classifier with synthetic fallback and optional local labeled CSV.
- `oracle/softcomputing/ga_test_priority.py` — seeded genetic test ordering with optional CI timing/coverage history.
- `data/labeled_logs.template.csv`, `data/oracle-test-history.template.json` — input templates; actual local data stays out of Git.
- `scripts/evaluate_log_classifier.py`, `docs/DATA_VALIDATION.md` — evaluation entry point and data guidance.
- `tests/test_softcomputing.py`, `tests/test_oracle_workflow.py` — current model/workflow coverage.

Current caveats: synthetic fallback data is not production validation; Bayes values are uncalibrated estimates; fuzzy scores are heuristic; GA coverage and timing are assumed when real history is absent. Keep those limitations visible in every report.

## 20 commit-sized tasks

1. **Document current model inputs and outputs** — Add concise module docs and known limitations. Files: `docs/MODEL_CARD.md`, `README.md`.
2. **Add baseline tests for Bayesian edge cases** — Cover zero overlap, full overlap and invalid confidence bounds. Files: `oracle/softcomputing/bayes_hypothesis.py`, `tests/test_softcomputing.py`.
3. **Add Bayesian explanation snapshots** — Ensure output reasons match the actual formula. Files: Bayes module and tests.
4. **Add fuzzy-rule boundary tests** — Test every severity boundary and score range. Files: `oracle/softcomputing/fuzzy_risk.py`, tests.
5. **Document fuzzy membership functions** — Explain membership inputs and rules with a small report example. Files: `docs/MODEL_CARD.md` or `docs/FUZZY_RISK.md`.
6. **Validate CSV rows with actionable messages** — Report malformed labels/empty text without printing sensitive log contents. Files: `log_classifier.py`, tests.
7. **Add class-balance checks** — Warn when labeled data is too imbalanced for meaningful evaluation. Files: `log_classifier.py`, `scripts/evaluate_log_classifier.py`, tests.
8. **Prevent evaluation leakage** — Ensure preprocessing and training occur inside each cross-validation fold. Files: `scripts/evaluate_log_classifier.py`, tests.
9. **Report a confusion matrix** — Add per-category error counts alongside macro F1 and baseline. Files: evaluation script, tests, `docs/DATA_VALIDATION.md`.
10. **Add deterministic MLP seed controls** — Make repeatable evaluation an explicit option and record it in output. Files: log classifier, evaluation script, tests.
11. **Add MLP model metadata** — Record training source, row count and evaluation date without storing raw logs. Files: log classifier, tests.
12. **Add confidence calibration study** — Compare predicted confidence against held-out outcomes; don’t call scores calibrated until evidence supports it. Files: evaluation script, tests, model card.
13. **Improve GA input validation** — Handle duplicate paths, invalid durations and malformed coverage values. Files: `ga_test_priority.py`, tests.
14. **Add GA stability evaluation** — Compare repeated seeded output and a simple deterministic baseline. Files: GA module, evaluation script or new script, tests.
15. **Add GA evaluation summary** — Report assumptions, test count and budget adherence clearly. Files: GA module, workflow tests.
16. **Validate CI history schema** — Reject malformed report rows and document ignored rows with reasons. Files: GA module, analyzer, tests.
17. **Add privacy checks for local training inputs** — Confirm real labeled logs and history files stay ignored and never appear in test output. Files: `.gitignore`, tests, `docs/DATA_VALIDATION.md`.
18. **Create a reproducible synthetic benchmark** — Keep fixtures clearly synthetic and separate from user-provided data. Files: `tests/fixtures/`, evaluation script.
19. **Add a model comparison report** — Compare simple baseline and MLP on the same held-out data; report limitations. Files: evaluation script, `docs/MODEL_CARD.md`.
20. **Review model claims across API and UI** — Coordinate with Teammate 2 and Iman so reported scores and limitations are consistent. Files: soft-computing modules, `oracle_api/workflow.py` only by coordination, `public/app.js` only by coordination, docs and tests.

## Commit and PR routine

Follow [`docs/TEAM_HANDOFF.md`](TEAM_HANDOFF.md). Never commit private logs, tokens, user datasets or generated model artifacts. Use synthetic fixtures for tests; report real-world accuracy only after a valid held-out evaluation on approved data.
