# ORACLE data and model validation

The current repository does not contain labeled incident logs or measured test-run history. ORACLE therefore uses its synthetic MLP demo corpus and filename-based, one-second test estimates until you supply real data. Do not describe those outputs as validated model performance.

## Train and evaluate the log classifier

1. Copy `data/labeled_logs.template.csv` to `data/labeled_logs.csv`.
2. Add redacted, representative log messages with one `message,category` row per example. Allowed labels are `validation`, `database`, `external_api`, `config`, `null_value`, `arithmetic`, `logic`, and `other`.
3. Add at least five examples in each of at least two categories before the web app trains on the local CSV. Keep raw or sensitive logs out of Git; `data/labeled_logs.csv` is ignored.
4. Evaluate with stratified cross-validation before relying on the predictions:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   python scripts\evaluate_log_classifier.py
   ```

The report includes accuracy, macro F1, and per-category precision, recall, and F1. It requires at least two examples per category. These metrics apply only to the examples you provide and do not guarantee performance on future logs.

## Provide measured test timings and coverage

Generate or collect the data in your trusted CI environment; ORACLE will not run tests. Add `oracle-test-history.json` to the root of the selected public repository using the shape in `data/oracle-test-history.template.json`:

- `id` must exactly match a discovered test-file path.
- `durationSeconds` should be a measured CI duration greater than 0 and at most 3,600 seconds.
- `covers` should contain source paths actually observed in per-test coverage data.

ORACLE reads only this small JSON report, applies rows that match discovered tests and scanned source files, and uses filename inference for unmatched fields. Review what the report contains before committing it; the selected repository is public in this MVP. The dashboard labels recorded timings and coverage separately from assumptions.

## Validation checklist

- Keep the held-out or cross-validation result separate from training examples when reporting model quality.
- Redact tokens, personal information, customer data, and internal hostnames from log examples.
- Compare the MLP with a simple majority-class baseline and inspect per-category errors before using it for decisions.
- Regenerate test-history metadata when the test suite changes; stale file paths are ignored.
- ORACLE remains read-only: it suggests a test order and never runs the repository's test commands.
