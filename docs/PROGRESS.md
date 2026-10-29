# ORACLE progress log

Paste this file at the start of every new Claude chat so it knows the project state.

## How we build

- **Step by step.** One small step at a time, each one becomes a PR on GitHub.
  Never generate the whole project at once.
- Each step: Claude writes the code + tests → we run them → commit → PR → merge → update this file.
- Full plan: the "ORACLE — Soft Computing Project Plan" doc (sections 1–12).

## Steps

| # | Step | Plan week | Status |
|---|---|---|---|
| 1 | Repo skeleton: README, licence, .gitignore, .env.example, requirements, CI, contributing guide | Week 0 | ✅ ready to push |
| 2 | Each member's first PR: add themselves to the README team table | Week 0 | ⏳ next |
| 3 | `oracle/models.py`: the shared data classes + tests | Week 1 | |
| 4 | `oracle/config.py`: settings from `.env` + tests | Week 1 | |
| 5 | Tool stubs (`tools/`) and soft computing stubs (`softcomputing/`) with owners | Week 1 | |

## Decisions

- Python only (3.11 / 3.12); Streamlit dashboard; SQLite; no Docker.
- Core works with no LLM (`LLM_PROVIDER=none`); LLM only rewrites the summary.
- Demo eshop repo is generated into `workspace/` (git-ignored), never committed.
