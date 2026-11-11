# ORACLE — a soft-computing bug investigator

ORACLE takes a bug report, looks through a repository's code, Git history and logs, and
produces a ranked list of root-cause hypotheses, a risk rating and a fix plan with the
tests to run first.

Its reasoning core is four soft computing techniques:

| Technique | Question it answers | Module |
|---|---|---|
| Bayesian belief updating | Which hypothesis is most likely, given the evidence? | `oracle/softcomputing/bayes_hypothesis.py` |
| Fuzzy inference (Mamdani) | How risky is this bug, how suspicious is this commit? | `oracle/softcomputing/fuzzy_risk.py` |
| Neural network (MLP) | What kind of error is this log line? | `oracle/softcomputing/log_classifier.py` |
| Genetic algorithm | Which tests should we run first? | `oracle/softcomputing/ga_test_priority.py` |

An LLM is optional (`LLM_PROVIDER` in `.env`). It only rewrites the final summary in
nicer words. It never decides the root cause, and ORACLE works fully offline without it.

> Soft Computing project · MCA Semester III · MNNIT Allahabad

## Status

🚧 **Week 0: setup.** The repository skeleton is in place; the modules above are built
week by week. See [`docs/PROGRESS.md`](docs/PROGRESS.md) for what is done and what is next.

## Web MVP: Node dashboard with FastAPI GitHub tools

The Node.js server handles GitHub sign-in, serves the dashboard, and forwards authenticated
scan requests to a local FastAPI service over loopback. FastAPI fetches repository metadata, the default-branch tree, and selected source files. A LangGraph workflow runs deterministic source checks, updates candidate-cause estimates with an explainable Bayesian odds calculation, scores risk with Mamdani fuzzy inference, classifies optional pasted logs with a one-hidden-layer MLP, and orders discovered test files with a genetic algorithm. The MLP uses bundled synthetic examples until a sufficiently labeled local CSV is supplied; scripts/evaluate_log_classifier.py reports stratified cross-validation metrics. The genetic algorithm uses recorded timings and per-test coverage from an optional repository report when available, otherwise it labels filename-derived coverage and assumed durations. See docs/DATA_VALIDATION.md for the data formats and validation steps. The dashboard shows evidence, scoring factors, suggested fixes, log labels, and a proposed test order. Bayesian estimates use hand-set rule scores and are not validated probabilities. The service stays bound to `127.0.0.1`; it does not send source or pasted logs to an LLM, execute repository code or tests, or make repository changes.

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
