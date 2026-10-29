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
| Rahul | @rahulparmar123942 | Dashboard + GA | Test prioritisation |

## How we built this

We used AI assistants (Claude) to help scaffold code, explain errors and review pull
requests. Every module was written, run and explained by its owner before merging.

## Licence

MIT — see `LICENSE`.
