# ORACLE — a soft-computing bug investigator

ORACLE takes an optional bug report, scans selected repository source files and optional
pasted logs, and produces ranked candidate findings, risk estimates, suggested fixes, and
a proposed test review order.

Its reasoning core is four soft computing techniques:

| Technique | Question it answers | Module |
|---|---|---|
| Bayesian belief updating | Which hypothesis is most likely, given the evidence? | `oracle/softcomputing/bayes_hypothesis.py` |
| Fuzzy inference (Mamdani) | How risky is this bug, how suspicious is this commit? | `oracle/softcomputing/fuzzy_risk.py` |
| Neural network (MLP) | What kind of error is this log line? | `oracle/softcomputing/log_classifier.py` |
| Genetic algorithm | Which tests should we run first? | `oracle/softcomputing/ga_test_priority.py` |

An optional RAG step retrieves relevant, redacted source excerpts locally for each
candidate finding. When enabled, a Gemini or local Ollama model uses those excerpts to
write a beginner-friendly explanation and a suggested fix. The deterministic checks
still create the findings; model output is advisory and requires human review.

> Soft Computing project · MCA Semester III · MNNIT Allahabad

## Status

🚧 **Week 0: setup.** The repository skeleton is in place; the modules above are built
week by week. See [`docs/PROGRESS.md`](docs/PROGRESS.md) for what is done and what is next.

## Web MVP: Node dashboard with FastAPI GitHub tools

The Node.js server handles GitHub sign-in, serves the dashboard, and forwards authenticated
scan requests to a local FastAPI service over loopback. FastAPI fetches repository metadata,
the default-branch tree, and selected source files. A LangGraph workflow runs deterministic
source checks, updates candidate-cause estimates with an explainable Bayesian odds
calculation, scores risk with Mamdani fuzzy inference, classifies optional pasted logs with
a one-hidden-layer MLP, orders discovered test files with a genetic algorithm, and retrieves
source context with local BM25 search. If `LLM_PROVIDER` is set to `gemini` or `ollama`,
ORACLE sends the issue description, finding details, and short retrieved excerpts for up
to five findings to that provider, then shows explanations alongside file and line citations.
Gemini is a hosted provider;
Ollama can run on the same computer. Common credential patterns are redacted before excerpts
are sent, but users should still review repository data and provider privacy terms. With
`LLM_PROVIDER=none`, ORACLE remains offline and shows retrieved excerpts without generated
explanations. No model can change the repository; ORACLE does not execute repository code or
tests. The MLP uses bundled synthetic examples until a sufficiently labeled local CSV is
supplied; scripts/evaluate_log_classifier.py reports stratified cross-validation metrics.
The genetic algorithm uses recorded timings and per-test coverage from an optional repository
report when available, otherwise it labels filename-derived coverage and assumed durations.
See docs/DATA_VALIDATION.md for data formats and validation steps. Bayesian estimates use
hand-set rule scores and are not validated probabilities.

### Enable RAG-grounded AI explanations

Copy `.env.example` to `.env` if you have not already. In `.env`, choose one provider:

```dotenv
# Local model (install Ollama and download the model first)
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2:3b

# Or a hosted Gemini model (keep the API key private)
# LLM_PROVIDER=gemini
# GEMINI_API_KEY=your-key
# GEMINI_MODEL=gemini-3.5-flash-lite
```

Restart the FastAPI terminal after changing `.env`, then run an investigation. Expand
“AI explanation and retrieved code” under a candidate finding to see the model explanation
and its source excerpts. With Ollama, the selected code stays on your computer if the Ollama
server is local. With Gemini, the retrieved excerpts are sent to Google for generation.
The GitHub access token remains on the local Node/FastAPI path and is never placed in the
LLM prompt. The AI can be unavailable and the original report still works.

Install the Python requirements once, then run the API and web app in separate VS Code terminals:

```powershell
python -m pip install -r requirements.txt
# Terminal 1
npm run api
# Terminal 2
npm start
```

The dashboard remains at `http://localhost:3000`; FastAPI's local API documentation is at
`http://127.0.0.1:8001/docs` while the API terminal is running. GitHub OAuth values stay in
the ignored `.env` file and are never sent to the browser.

### Publish on Render's free plan (Ollama stays local)

The root `render.yaml` creates **one free Docker web service**. The container runs the
Node dashboard and FastAPI together, with FastAPI available only inside the container.
The hosted service sets `LLM_PROVIDER=none`, so Ollama is used only for local runs and
hosted investigations show deterministic findings and retrieved code without generated
AI explanations.

1. Push the deployment files on your project branch to GitHub, then create a Render
   Blueprint for that branch using the root `render.yaml`. Choose the **Free** plan if
   Render asks for a plan.
2. Enter `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` when prompted. Render generates
   `SESSION_SECRET` for the service.
3. Once the service has a public URL, set your GitHub OAuth app's homepage to
   `https://YOUR-ORACLE-URL/` and callback to
   `https://YOUR-ORACLE-URL/auth/callback`.
4. Open the Render URL and connect GitHub. Repository analysis is read-only.

Render's free service sleeps after about 15 minutes without traffic, so the first visit
after idling can take a while. Its filesystem is temporary and its memory/CPU allowance
is small; large repository investigations may be slow or run out of memory. This is a
free demonstration deployment, not a production availability guarantee. Do not publish
`.env` or put OAuth secrets in `render.yaml`. Render supplies the public URL through
`RENDER_EXTERNAL_URL`; local development continues to use `APP_URL` or localhost.

## Set up on your laptop

You need Python 3.11 or 3.12, Git and VS Code.

```bash
git clone https://github.com/<owner>/oracle.git
cd oracle
python -m venv venv
# Windows:      venv\Scripts\activate
# macOS/Linux:  source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env               # Windows: copy .env.example .env
pytest                             # should print "1 passed"
```

## Team

Each member adds their own row in their first pull request (see `docs/CONTRIBUTING.md`).

| Member | GitHub | Role | Soft computing module |
|---|---|---|---|

## How we built this

We used AI assistants (Claude) to help scaffold code, explain errors and review pull
requests. Every module was written, run and explained by its owner before merging.

## Licence

MIT — see `LICENSE`.
