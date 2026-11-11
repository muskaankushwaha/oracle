# Teammate 2 — FastAPI, analyzer and LangGraph plan

**Ownership:** Python API endpoints, read-only source analyzer, evidence structure and LangGraph orchestration. Replace this heading with the contributor’s name and GitHub handle.

## Existing code in this area

- `oracle_api/main.py` — FastAPI health and repository analysis endpoints.
- `oracle_api/analyzer.py` — bounded source-file checks, findings, evidence redaction and test discovery.
- `oracle_api/workflow.py` — current fixed LangGraph sequence: scan, classify supplied logs, rank evidence, prioritize tests, publish report.
- `tests/test_oracle_api.py`, `tests/test_oracle_workflow.py` — API and workflow coverage.
- `requirements.txt`, `pyproject.toml` — Python dependencies and project setup.

The current workflow is a deterministic pipeline; it is not yet an autonomous LLM agent. Keep repository operations read-only and do not run tests or repository code fetched from GitHub.

## 20 commit-sized tasks

1. **Document FastAPI request and response schemas** — Define concrete Pydantic models for current inputs and outputs. Files: `oracle_api/main.py`, new `oracle_api/schemas.py`, `tests/test_oracle_api.py`.
2. **Validate analysis request limits centrally** — Cover missing values, oversized logs and malformed owner/repository names. Files: `oracle_api/main.py`, `tests/test_oracle_api.py`.
3. **Add GitHub fetch timeout and retry policy** — Bound network waits and retry only safe transient reads. Files: `oracle_api/main.py` or new `oracle_api/github_client.py`, tests.
4. **Add tests for file and byte scan caps** — Verify the analyzer stops exactly at configured limits. Files: `oracle_api/analyzer.py`, `tests/test_oracle_api.py`.
5. **Add language-aware finding fixtures** — Create small synthetic fixtures for each supported rule. Files: `tests/fixtures/`, `tests/test_oracle_api.py`.
6. **Improve finding identity stability** — Use stable IDs derived from rule and source location. Files: `oracle_api/analyzer.py`, tests.
7. **Strengthen secret redaction tests** — Cover common key formats and ensure evidence never returns matched secret values. Files: analyzer and tests.
8. **Return explicit skipped-file reasons** — Distinguish ignored, unsupported and unreadable paths without leaking content. Files: `oracle_api/analyzer.py`, schemas and tests.
9. **Add finding schema version** — Version API findings before frontend or data consumers rely on them. Files: schemas, analyzer, tests.
10. **Add tests for GitHub tree truncation** — Ensure capped or truncated trees are represented clearly. Files: `oracle_api/main.py`, tests.
11. **Separate tool functions from HTTP routes** — Keep route handling small and inject GitHub reads for tests. Files: `oracle_api/main.py`, new GitHub tool module.
12. **Add LangGraph investigation plan state** — Track selected tool names and reasons in typed state. Files: `oracle_api/workflow.py`, workflow tests.
13. **Add deterministic conditional routing** — Skip log classification when no logs are provided and skip test ranking when there are no test candidates. Files: workflow and tests.
14. **Add bounded evidence follow-up** — Allow one targeted second pass only when a result is inconclusive and a safe read-only signal exists. Set a hard iteration limit and test it. Files: workflow and tests.
15. **Add finding verifier node** — Reject report claims without matching repository path/line evidence or supplied-log evidence. Files: workflow, analyzer and tests.
16. **Add graph execution trace** — Return node names and stop reasons without secrets or raw source content. Files: workflow, schemas and tests.
17. **Add per-investigation time/tool budget** — Stop gracefully when a configured budget is reached. Files: workflow, config and tests.
18. **Test empty, partial and failed graph runs** — Ensure errors and missing optional inputs still produce safe, honest reports. Files: `tests/test_oracle_workflow.py`.
19. **Document agentic boundaries** — Explain planner, tool router, verifier, limits and human approval before any future repository write. Files: `docs/AGENT_WORKFLOW.md`, `README.md`.
20. **Integrate Node/API response contract** — Coordinate schema changes with Teammate 1 and Iman; update contract tests and docs. Files: `oracle_api/`, `server.js` only by coordination, tests and `docs/API_CONTRACT.md`.

## Commit and PR routine

Follow [`docs/TEAM_HANDOFF.md`](TEAM_HANDOFF.md). Create small branches, keep API responses backward-compatible where possible, and include tests for each behavior. Any future repository write or PR feature needs explicit user approval and a separate review.
