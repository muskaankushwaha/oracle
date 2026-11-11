# Rollback checkpoints

Tell Codex: **"Roll back to `<checkpoint-name>`"**. It restores only that checkpoint's listed files and preserves unrelated changes.

| Name | Saved state | Files restored |
|---|---|---|
| `before-code-submission-bundles` | Team handoff before adding four code snippet bundles | `docs/TEAM_HANDOFF.md`, `docs/ORACLE_CHANGELOG.md`, `docs/ROLLBACK_CHECKPOINTS.md`, `.oracle-history/restore-ui-baseline.ps1`; removes `docs/CODE_SUBMISSION_IMAN.md` and `docs/CODE_SUBMISSION_MEMBER_1.md` through `docs/CODE_SUBMISSION_MEMBER_3.md` |
| `before-team-work-plans` | Existing handoff notes before adding four role-based GitHub plans | `docs/TEAM_HANDOFF.md`, `docs/ORACLE_CHANGELOG.md`, `docs/ROLLBACK_CHECKPOINTS.md`, `.oracle-history/restore-ui-baseline.ps1`; removes `docs/TEAM_IMAN.md` and `docs/TEAM_MEMBER_1.md` through `docs/TEAM_MEMBER_3.md` |
| `before-settings-logout` | Dashboard before moving logout into the Settings account screen | `server.js`, `public/index.html`, `public/app.js`, `public/styles.css`, `docs/ORACLE_CHANGELOG.md`, `docs/ROLLBACK_CHECKPOINTS.md`, `.oracle-history/restore-ui-baseline.ps1` |
| `before-visible-logout` | Dashboard before making the existing GitHub logout action visible | `public/app.js`, `public/styles.css`, `docs/ORACLE_CHANGELOG.md`, `docs/ROLLBACK_CHECKPOINTS.md`, `.oracle-history/restore-ui-baseline.ps1` |
| `stable-ui` | 2026-10-31 interface baseline with original logo, theme toggle, and severity filter | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-day-night-transition` | Compact moon/sun switch before the scene redesign | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-minimal-scene-toggle` | Scene switch before removing visible text and outer frame | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-narrow-toggle` | 56px toggle before its first width reduction | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-length-reduction` | 56px toggle before the later 50px length adjustment | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-height-reduction` | 50px by 30px toggle before the height update | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-premium-canvas` | UI before the warm off-white light-mode background | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-logo-fluid` | UI before first logo liquid effect | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-ring-fluid` | Static logo before first annular-fluid attempt | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-annular-fluid` | Static logo before the outer-to-inner-circle effect | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-full-ring-fluid` | Normal static logo before filling the full ring band | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-violet-ring-fluid` | Full-ring fluid with extra ring outlines, before keeping only the original violet band | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-public-repo-input` | GitHub repository dropdown before adding paste-by-URL selection | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-light-sidebar-contrast` | Sidebar before stronger light-mode hover contrast | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-active-light-hover` | Sidebar before the selected-item hover correction | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-sidebar-edge-removal` | Sidebar before removing the light-mode hover accent stripe | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-light-repo-menu` | Repository selector before light-mode native menu colors | `public/index.html`, `public/app.js`, `public/styles.css` |
| `before-fastapi-github-tool` | Node-only repository scan before adding the FastAPI GitHub tree service | `server.js`, `requirements.txt`, `README.md`, `package.json`; removes `oracle_api/main.py` and `oracle_api/__init__.py` |
| `before-fastapi-analysis-engine` | FastAPI tree tool before moving file downloads and finding analysis from Node | `server.js`, `README.md`, `oracle_api/main.py`; removes `oracle_api/analyzer.py` and `tests/test_oracle_api.py` |
| `before-langgraph-investigation` | FastAPI rule scan before adding the issue-aware LangGraph workflow | `server.js`, `requirements.txt`, `README.md`, `oracle_api/main.py`, `public/index.html`, `public/app.js`, `public/styles.css`; removes `oracle_api/workflow.py` and `tests/test_oracle_workflow.py` |
| `before-langgraph-final-polish` | LangGraph workflow UI copy and test assertion before final verification updates | `public/index.html`, `tests/test_oracle_workflow.py`, `docs/ORACLE_CHANGELOG.md`, `docs/ROLLBACK_CHECKPOINTS.md`, `.oracle-history/restore-ui-baseline.ps1` |
| `before-bayesian-fuzzy-integration` | Issue-aware LangGraph workflow before Bayesian candidate updates and Mamdani fuzzy risk scoring | `oracle_api/workflow.py`, `public/app.js`, `README.md`, `tests/test_oracle_workflow.py`, `docs/ORACLE_CHANGELOG.md`, `docs/ROLLBACK_CHECKPOINTS.md`, `.oracle-history/restore-ui-baseline.ps1`; removes `oracle/softcomputing/__init__.py`, `oracle/softcomputing/bayes_hypothesis.py`, `oracle/softcomputing/fuzzy_risk.py`, and `tests/test_softcomputing.py` |
| `before-mlp-ga-integration` | Bayesian/fuzzy investigation before MLP log classification and genetic-algorithm test ordering | `oracle/softcomputing/__init__.py`, `oracle/softcomputing/bayes_hypothesis.py`, `oracle_api/analyzer.py`, `oracle_api/main.py`, `oracle_api/workflow.py`, `public/index.html`, `public/app.js`, `public/styles.css`, `tests/test_oracle_api.py`, `tests/test_oracle_workflow.py`, `tests/test_softcomputing.py`, `README.md`, `docs/ORACLE_CHANGELOG.md`, `docs/ROLLBACK_CHECKPOINTS.md`, `server.js`, `.oracle-history/restore-ui-baseline.ps1`; removes `oracle/softcomputing/log_classifier.py` and `oracle/softcomputing/ga_test_priority.py` |
| `before-real-data-validation` | MLP/GA demo behavior before adding labeled-data evaluation and optional CI history ingestion | `oracle/softcomputing/log_classifier.py`, `oracle/softcomputing/ga_test_priority.py`, `oracle_api/analyzer.py`, `public/app.js`, `.gitignore`, `README.md`, `tests/test_softcomputing.py`, `tests/test_oracle_api.py`, `docs/ORACLE_CHANGELOG.md`, `docs/ROLLBACK_CHECKPOINTS.md`, `.oracle-history/restore-ui-baseline.ps1`; removes `scripts/evaluate_log_classifier.py`, `docs/DATA_VALIDATION.md`, `data/labeled_logs.template.csv`, and `data/oracle-test-history.template.json` |
| `before-llm-rag-20261111` | Read-only LangGraph investigation before adding local source retrieval and optional Gemini/Ollama explanations | `.env.example`, `README.md`, `requirements.txt`, `oracle/config.py`, `oracle_api/analyzer.py`, `oracle_api/main.py`, `oracle_api/workflow.py`, `oracle_api/llm.py`, `oracle_api/rag.py`, `public/app.js`, `public/styles.css`, `docs/ORACLE_CHANGELOG.md`, `docs/ROLLBACK_CHECKPOINTS.md`, `.oracle-history/restore-ui-baseline.ps1` |
| `before-render-hosting-20261111` | Local ORACLE setup before adding Render deployment configuration | `server.js`, `render.yaml`, `README.md`, `docs/ORACLE_CHANGELOG.md`, `docs/ROLLBACK_CHECKPOINTS.md`, `.oracle-history/restore-ui-baseline.ps1` |

Snapshots are local under `.oracle-history/` and ignored by Git. Restore one with:

```powershell
powershell -NoProfile -File .\.oracle-history\restore-ui-baseline.ps1 -Checkpoint before-violet-ring-fluid
```

The script asks for `RESTORE` before overwriting files. Before future edits, create a new immutable named snapshot, add it to this table and the restore script map, and log the change in `docs/ORACLE_CHANGELOG.md`.
