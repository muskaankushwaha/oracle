# ORACLE change log

## 2026-11-11 - Create GitHub project README and screenshot gallery

- Replaced the outdated setup-status README with a complete project overview covering the current MVP, architecture, AI methods, safety boundaries, local setup, configuration, team, and repository structure.
- Added nine interface screenshots under `docs/images/oracle-screenshots/` and embedded them in the README gallery.
- Changed `README.md`, `docs/ORACLE_CHANGELOG.md`, `docs/ROLLBACK_CHECKPOINTS.md`, `.oracle-history/restore-ui-baseline.ps1`, and added the screenshot assets. Pre-change checkpoint: `before-readme-showcase-20261111`.
- Registered the checkpoint in the rollback index and restore script.

## 2026-11-11 - Use a single free Render service

- Replaced the separate public Node and paid private API services with one free Docker web service that runs Node and FastAPI together. The hosted service keeps `LLM_PROVIDER=none`; Ollama remains available for local use.
- Added a minimal Render Python dependency list, container setup, process launcher, and Docker ignore rules. Updated deployment instructions with OAuth setup and free-tier sleep/resource limits.
- Changed `render.yaml`, `server.js`, `README.md`, `Dockerfile`, `.dockerignore`, `requirements-render.txt`, `start-render.sh`, `docs/ORACLE_CHANGELOG.md`, `docs/ROLLBACK_CHECKPOINTS.md`, and `.oracle-history/restore-ui-baseline.ps1`. Pre-change checkpoint: `before-render-free-single-service-20261111`.
- Registered the checkpoint in the rollback index and restore script.

## 2026-11-11 - Prepare Render deployment with hosted AI disabled

- Added a Render Blueprint for a public Node dashboard and private FastAPI service, with a generated session secret, dashboard-to-API private host wiring, GitHub OAuth secrets entered in Render, and `LLM_PROVIDER=none` on the hosted API.
- Made the Node server use Render's generated external URL for the GitHub OAuth callback and accept the private service host:port while preserving localhost defaults. Documented deployment and OAuth callback setup.
- Changed `server.js`, `render.yaml`, `README.md`, `docs/ORACLE_CHANGELOG.md`, `docs/ROLLBACK_CHECKPOINTS.md`, and `.oracle-history/restore-ui-baseline.ps1`. Pre-change checkpoint: `before-render-hosting-20261111`.
- Registered the checkpoint in the rollback index and restore script.

## 2026-11-11 - Add RAG-grounded LLM explanations

- Added local BM25 retrieval over bounded source chunks, with common credential redaction and file/line citations. The LangGraph investigation now retrieves relevant excerpts for candidate findings and displays them in the dashboard.
- Added opt-in Gemini and Ollama providers. A configured model receives the issue description, finding details, and retrieved excerpts for at most five findings; the GitHub token and full repository are excluded. Gemini is hosted; Ollama can run locally. Model explanations and fixes remain advisory, and provider failures do not stop the deterministic report.
- Changed `.env.example`, `README.md`, `requirements.txt`, `oracle/config.py`, `oracle_api/analyzer.py`, `oracle_api/main.py`, `oracle_api/workflow.py`, `oracle_api/llm.py`, `oracle_api/rag.py`, `public/app.js`, and `public/styles.css`. Pre-change checkpoint: `before-llm-rag-20261111`.
- Registered the checkpoint in `docs/ROLLBACK_CHECKPOINTS.md` and `.oracle-history/restore-ui-baseline.ps1`.

## 2026-11-01 - Prepare four code submission bundles

- Added four contributor-specific files with 20 code snippets each, suggested commit messages, target source paths, and progress comments: frontend (`Iman`), Node/GitHub (`Teammate 1`), FastAPI/LangGraph (`Teammate 2`), and soft computing/evaluation (`Teammate 3`).
- The snippets are starter submissions for contributors to review, adapt, test, and commit individually; they are not integrated in ORACLE yet. Added links from `docs/TEAM_HANDOFF.md`.
- Changed `docs/TEAM_HANDOFF.md`, `docs/CODE_SUBMISSION_IMAN.md`, `docs/CODE_SUBMISSION_MEMBER_1.md`, `docs/CODE_SUBMISSION_MEMBER_2.md`, and `docs/CODE_SUBMISSION_MEMBER_3.md`. Pre-change checkpoint: `before-code-submission-bundles`.
- Registered the checkpoint in `docs/ROLLBACK_CHECKPOINTS.md` and `.oracle-history/restore-ui-baseline.ps1`.

## 2026-11-01 - Create four-person GitHub work plans

- Replaced the outdated team handoff with a four-owner index, a safe baseline-publishing guide, and separate 20-task plans for Iman (frontend/integration), Teammate 1 (Node/GitHub), Teammate 2 (FastAPI/LangGraph), and Teammate 3 (soft computing/evaluation).
- Recorded the current Git status/remote context and warned that the local MVP must be reviewed and merged as a baseline PR before teammates can pull it. Included safe staging guidance that excludes `.env`, `.oracle-history/`, and the unexplained `oracle/config.py` change.
- Added `docs/TEAM_IMAN.md`, `docs/TEAM_MEMBER_1.md`, `docs/TEAM_MEMBER_2.md`, and `docs/TEAM_MEMBER_3.md`; updated `docs/TEAM_HANDOFF.md`. Pre-change checkpoint: `before-team-work-plans`.
- Registered the checkpoint in `docs/ROLLBACK_CHECKPOINTS.md` and `.oracle-history/restore-ui-baseline.ps1`.

## 2026-11-01 - Move logout into account Settings

- Removed the logout control beside the top-bar profile image and made the Settings navigation open a focused account card with the GitHub profile image, display name, email, and logout button.
- Requested GitHub's `user:email` OAuth scope and load the primary verified email for the account card. If GitHub provides no email, the card displays “Email unavailable.”
- Changed `server.js`, `public/index.html`, `public/app.js`, and `public/styles.css`. Pre-change checkpoint: `before-settings-logout`.
- Registered the checkpoint in `docs/ROLLBACK_CHECKPOINTS.md` and `.oracle-history/restore-ui-baseline.ps1`.

## 2026-11-01 - Make GitHub logout visible

- Added an explicit, keyboard-accessible **Log out** button beside the signed-in user's avatar. It calls the existing server-side logout endpoint, which invalidates the session and clears its cookie; errors are shown without silently leaving the page.
- Changed `public/app.js` and `public/styles.css`. Pre-change checkpoint: `before-visible-logout`.
- Registered the checkpoint in `docs/ROLLBACK_CHECKPOINTS.md` and `.oracle-history/restore-ui-baseline.ps1`.

This log records the local ORACLE web MVP work in `D:\Oracle`. Keep a new dated entry here before each future change so the old state is recorded first.

## 2026-10-31 - UI baseline and current features

A local UI snapshot was captured at `.oracle-history/ui-baseline-2026-10-31/`. It contains `public/index.html`, `public/app.js`, and `public/styles.css`. The folder is ignored by Git. To restore those three files, run `powershell -NoProfile -File .\.oracle-history\restore-ui-baseline.ps1` from the project root and type `RESTORE` when prompted.

Current changes recorded:

- The web MVP uses GitHub OAuth and repository selection, then performs a read-only source scan and displays findings, evidence, severity, and fix suggestions (`server.js`, `package.json`, `public/`).
- The findings panel has a severity filter that works with search (`public/index.html`, `public/app.js`, `public/styles.css`).
- The dark/light theme selection is saved in browser storage (`public/app.js`, `public/styles.css`).
- The theme button is an animated day/night scene transition with reduced-motion support (`public/index.html`, `public/app.js`, `public/styles.css`).
- The original ring-and-dot logo was restored. Its center changes to the light surface color in light mode (`public/index.html`, `public/styles.css`).

No pull request or push was made. `oracle/config.py` already had a separate local modification; keep it out of the web MVP handoff unless its author requests it.

## Future entries

Before editing, copy the current `public/index.html`, `public/app.js`, and `public/styles.css` into a new dated folder under `.oracle-history/`, add a restore script for that snapshot, and append the change summary here. Never overwrite an existing snapshot.
## Named rollback point

- `stable-ui` is the named checkpoint for the current interface. It restores `public/index.html`, `public/app.js`, and `public/styles.css` from `.oracle-history/ui-baseline-2026-10-31/`.
- Use `docs/ROLLBACK_CHECKPOINTS.md` as the checkpoint index. When the user says "roll back to <name>", restore only the files assigned to that name.
## 2026-10-31 - Animated day/night toggle

- Checkpoint saved before this change: `before-day-night-transition` (`.oracle-history/before-day-night-transition/`).
- Updated only the theme toggle markup, state label logic, and toggle-specific CSS in `public/index.html`, `public/app.js`, and `public/styles.css`.
- The switch animates between a night sky with stars and a daylight sky with sunrise and clouds. Reduced-motion preferences disable the animation.
## 2026-10-31 - Minimal day/night toggle

- Checkpoint saved before this change: `before-minimal-scene-toggle` (`.oracle-history/before-minimal-scene-toggle/`).
- Removed the visible Day/Night text and the outer button frame. The animated day/night scene remains the clickable toggle.
- Changed only toggle markup, toggle label logic, and toggle-specific styles (`public/index.html`, `public/app.js`, `public/styles.css`).
## 2026-10-31 - Narrower day/night toggle

- Checkpoint saved before this change: `before-narrow-toggle` (`.oracle-history/before-narrow-toggle/`).
- Reduced the scene and button width from 56px to 50px and adjusted two star positions. Changed only `public/styles.css`.
## 2026-10-31 - Shorter day/night toggle

- Checkpoint saved before this change: `before-length-reduction` (`.oracle-history/before-length-reduction/`).
- Reduced the toggle length from 56px to 50px and repositioned two stars so the scene stays balanced. Changed only `public/styles.css`.
## 2026-10-31 - Restore toggle length and reduce height

- Checkpoint saved before this change: `before-height-reduction` (`.oracle-history/before-height-reduction/`), capturing the current 50px by 30px version.
- Restored the scene width to 56px and reduced the scene and button height from 30px to 26px. Changed only `public/styles.css`.
## 2026-10-31 - Roll back toggle height

- Restored `public/styles.css` from `before-height-reduction`; the toggle is back to 50px by 30px.
## 2026-10-31 - Restore original day/night toggle size

- Restored `public/styles.css` from `before-narrow-toggle`; the animated scene is 56px by 30px again.
- Kept the current day/night scene, text-free button, and theme behavior.
## 2026-10-31 - Premium off-white light canvas

- Checkpoint saved before this change: `before-premium-canvas` (`.oracle-history/before-premium-canvas/`).
- Changed the light-mode page background token from cool gray to warm off-white (`#f7f5f0`). No panel or logo colors changed.
## 2026-10-31 - Interactive fluid logo

- Checkpoint saved before this change: `before-logo-fluid` (`.oracle-history/before-logo-fluid/`).
- Added a clipped animated liquid fill inside the existing logo ring. Pointer height controls the fill level; keyboard focus raises it; it settles on pointer leave or blur. Reduced-motion settings disable the wave animation.
- Changed only the logo markup and behavior (`public/index.html`, `public/app.js`) and logo-specific styles (`public/styles.css`).
## 2026-10-31 - Roll back interactive fluid logo

- Restored `public/index.html`, `public/app.js`, and `public/styles.css` from `before-logo-fluid`.
- The static ring-and-dot logo is back; the day/night toggle and other UI are preserved.
## 2026-10-31 - Fluid ring channel

- Checkpoint saved before this change: `before-ring-fluid` (`.oracle-history/before-ring-fluid/`).
- Added the liquid animation clipped to the annular band between the logo's outer ring and center, leaving the center dot unchanged. Pointer height controls the liquid level; keyboard focus raises it; reduced-motion settings stop the wave animation.
- Changed only the logo markup, pointer behavior, and logo-specific CSS (`public/index.html`, `public/app.js`, `public/styles.css`).
## 2026-10-31 - Roll back ring-fluid logo

- Restored `public/index.html`, `public/app.js`, and `public/styles.css` from `before-ring-fluid`.
- The static ring-and-dot logo is back; all other UI features match that checkpoint.
## 2026-10-31 - Fluid between logo circles

- Checkpoint saved before this change: `before-annular-fluid` (`.oracle-history/before-annular-fluid/`).
- Added animated liquid clipped to the annular channel between the logo's outer ring and inner circle. The center remains clear. Pointer height controls the fill level; keyboard focus raises it; reduced-motion settings stop the wave animation.
- Changed only the logo markup, pointer behavior, and logo-specific CSS (`public/index.html`, `public/app.js`, `public/styles.css`).
## 2026-10-31 - Restore normal logo

- Restored `public/index.html`, `public/app.js`, and `public/styles.css` from `before-annular-fluid`.
- Removed the fluid effect; the normal static ring-and-dot logo is restored.
## 2026-10-31 - Fluid fill across logo ring

- Checkpoint saved before this change: `before-full-ring-fluid` (`.oracle-history/before-full-ring-fluid/`).
- Filled the full annular band between the logo's outer circle and inner circle with animated fluid texture. The center hole stays empty; hover or keyboard focus speeds the flow and brightens it.
- Changed only the logo markup and logo-specific styles (`public/index.html`, `public/styles.css`). Reduced-motion preferences stop the animation.
## 2026-10-31 - Violet fluid inside the existing logo band

- Removed the added inner and outer outline strokes that made the logo look like it had extra circles.
- Kept the fluid clipped to the existing ring band and shifted its flowing colors and highlights to violet.
- Changed only public/index.html and public/styles.css. Pre-change checkpoint: before-violet-ring-fluid.


## 2026-10-31 - Restore normal logo

- Restored public/index.html and public/styles.css from before-full-ring-fluid; the logo is static again with no fluid effect.
- Kept the current public/app.js and unrelated UI changes in place.


## 2026-10-31 - Scan any public GitHub repository

- Added a dashboard field for a public GitHub URL or `owner/repo`, alongside the connected account repository selector.
- Validated pasted repository URLs in the browser and reused the existing server-side, read-only source scanner; private repositories remain unsupported.
- Changed `public/index.html`, `public/app.js`, and `public/styles.css`. Pre-change checkpoint: `before-public-repo-input`.

## 2026-11-01 - Improve light-mode sidebar hover contrast

- Replaced the pale hover treatment with a clearer lavender background, darker label and icon colors, and a visible accent edge. Active selection remains distinct.
- Changed only public/styles.css. Pre-change checkpoint: before-light-sidebar-contrast.


## 2026-11-01 - Keep selected sidebar item visible on hover

- Added a dedicated light-mode selected-and-hovered state with a stronger violet surface, white text and icon, and a pale accent edge. The active selection stays high contrast while hovered.
- Changed only `public/styles.css`. Pre-change checkpoint: `before-active-light-hover`.

## 2026-11-01 - Remove the sidebar hover accent stripe

- Removed the contrasting left-edge stripe from the light-mode hover states. The violet hover background and readable labels remain.
- Changed only `public/styles.css`. Pre-change checkpoint: `before-sidebar-edge-removal`.

## 2026-11-01 - Match repository menu to light mode

- Set the native repository selector to a light color scheme and gave its options a white surface with dark readable text.
- Changed only `public/styles.css`. Pre-change checkpoint: `before-light-repo-menu`.

## 2026-11-01 - Add FastAPI GitHub repository-tree tool

- Added a loopback-only FastAPI service with a read-only GitHub repository metadata and tree endpoint. It receives the signed-in user's token from the Node server, fetches the default-branch tree, validates repository names, and caps returned entries.
- Routed the existing scan through this tool while keeping the Node dashboard, file-content reads, and heuristic findings flow intact. Added an `npm run api` command and setup steps for the two local services.
- Changed `oracle_api/main.py`, `oracle_api/__init__.py`, `server.js`, `requirements.txt`, `package.json`, and `README.md`. Pre-change checkpoint: `before-fastapi-github-tool`.
- Registered the rollback snapshot in docs/ROLLBACK_CHECKPOINTS.md and .oracle-history/restore-ui-baseline.ps1.

## 2026-11-01 - Move repository scan analysis into FastAPI

- Moved the existing deterministic checks, source-file downloads, evidence redaction, severity ordering, and finding construction from Node into `oracle_api/analyzer.py` and the FastAPI analyze endpoint. Node retains GitHub OAuth, session protection, and dashboard/API forwarding.
- Added tests for line evidence, credential redaction, and read-only repository analysis. The Python scan remains heuristic; no trained deep-learning model or LangGraph agent was added.
- Changed `oracle_api/main.py`, `oracle_api/analyzer.py`, `server.js`, `README.md`, and `tests/test_oracle_api.py`. Pre-change checkpoint: `before-fastapi-analysis-engine`.
- Registered the checkpoint in `docs/ROLLBACK_CHECKPOINTS.md` and `.oracle-history/restore-ui-baseline.ps1`.

## 2026-11-01 - Complete issue-aware LangGraph investigation slice

- Connected the optional issue description through the dashboard and FastAPI into a LangGraph pipeline that runs the existing read-only rule scanner, then ranks findings by rule confidence, severity, and issue-term overlap. Candidate explanations show source evidence, matched terms, scoring reasons, and fix suggestions; the UI labels them as candidates rather than confirmed causes.
- Added workflow coverage and clarified the loading message. This remains deterministic, uses no external model, and does not claim deep-learning explainability. Install updated Python requirements in the project's virtual environment before restarting both services.
- Changed `oracle_api/workflow.py`, `oracle_api/main.py`, `server.js`, `requirements.txt`, `public/index.html`, `public/app.js`, `public/styles.css`, `tests/test_oracle_workflow.py`, and `README.md`. Pre-change checkpoint: `before-langgraph-investigation`.
- Registered the pre-verification polish checkpoint in `docs/ROLLBACK_CHECKPOINTS.md` and `.oracle-history/restore-ui-baseline.ps1`.

## 2026-11-01 - Add Bayesian hypothesis updates and fuzzy risk scoring

- Added a Bayesian odds update that combines each detector's hand-set confidence proxy with issue-term overlap, returning the prior, likelihood ratio, posterior estimate, and explanation. Added Mamdani fuzzy inference combining severity, rule confidence, and the posterior into a separate 0-100 risk score with rule activations.
- Connected both methods to the LangGraph workflow and dashboard. Candidate rows now show the Bayesian estimate and fuzzy risk; the overall risk card uses the highest fuzzy score. The API explicitly warns that the hand-set values are not calibrated probabilities. GitHub repository access remains read-only and no external model receives source code.
- Added unit and workflow tests. Changed `oracle/softcomputing/__init__.py`, `oracle/softcomputing/bayes_hypothesis.py`, `oracle/softcomputing/fuzzy_risk.py`, `oracle_api/workflow.py`, `public/app.js`, `README.md`, `tests/test_oracle_workflow.py`, and `tests/test_softcomputing.py`. Pre-change checkpoint: `before-bayesian-fuzzy-integration`.
- Registered the checkpoint in `docs/ROLLBACK_CHECKPOINTS.md` and `.oracle-history/restore-ui-baseline.ps1`.

## 2026-11-01 - Add MLP log labels and genetic test ordering

- Added a one-hidden-layer scikit-learn MLP classifier for optional pasted log lines. It uses 64 bundled synthetic examples, reports lexical cues, limits analysis to 100 lines, and warns that its scores are uncalibrated and labels need review. User logs are processed locally and are not used to train the model.
- Added a seeded genetic algorithm that orders repository test files by inferred source-file coverage and finding risk, subject to a time budget. Test coverage is inferred from file names and each duration defaults to an assumed one second because run history is unavailable. ORACLE only recommends tests; it does not execute repository code.
- Connected optional log input, classifications, and prioritized test files to the FastAPI/LangGraph flow and dashboard. Added tests for model labels, repository test discovery, risk-oriented ordering, deterministic output, and time-budget behavior.
- Changed `oracle/softcomputing/__init__.py`, `oracle/softcomputing/log_classifier.py`, `oracle/softcomputing/ga_test_priority.py`, `oracle_api/analyzer.py`, `oracle_api/main.py`, `oracle_api/workflow.py`, `server.js`, `public/index.html`, `public/app.js`, `public/styles.css`, `tests/test_oracle_api.py`, `tests/test_oracle_workflow.py`, `tests/test_softcomputing.py`, and `README.md`. Pre-change checkpoint: `before-mlp-ga-integration`.
- Registered the checkpoint in `docs/ROLLBACK_CHECKPOINTS.md` and `.oracle-history/restore-ui-baseline.ps1`.

## 2026-11-01 - Add real-data validation hooks for MLP and GA

- Added local `data/labeled_logs.csv` loading for the MLP when at least five labeled examples per class and two classes are present; otherwise it explicitly falls back to bundled synthetic examples. Added a stratified cross-validation script reporting accuracy, macro F1, per-category metrics, and a majority-class baseline.
- Added support for an optional `oracle-test-history.json` report in a selected public repository. Matching discovered tests can carry measured durations and per-test source coverage into the GA; absent or invalid rows remain labeled as inferred/assumed. ORACLE only reads the report and still never executes tests.
- Added empty templates, data-handling guidance, and tests for CSV training/evaluation and CI report ingestion. No labeled production logs or real CI timings were present in this project, so no real-world accuracy or timing claim is made.
- Changed `oracle/softcomputing/log_classifier.py`, `oracle/softcomputing/ga_test_priority.py`, `oracle_api/analyzer.py`, `public/app.js`, `.gitignore`, `README.md`, `tests/test_softcomputing.py`, `tests/test_oracle_api.py`, `scripts/evaluate_log_classifier.py`, `data/labeled_logs.template.csv`, `data/oracle-test-history.template.json`, and `docs/DATA_VALIDATION.md`. Pre-change checkpoint: `before-real-data-validation`.
- Registered the checkpoint in `docs/ROLLBACK_CHECKPOINTS.md` and `.oracle-history/restore-ui-baseline.ps1`.
