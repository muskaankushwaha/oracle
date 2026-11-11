# Teammate 2 — full FastAPI/LangGraph code submission

## Code file

Use the full source module at [`oracle_api/agentic_planner.py`](../oracle_api/agentic_planner.py). It adds a deterministic bounded planner, optional log/test routing decisions, a step and time budget, a single limited follow-up decision, source-line evidence checks, safe action tracing, and explicit stop/disclaimer helpers.

## Progress notes

The source contains 20 `Progress 01/20` through `Progress 20/20` comments for the implementation sections. The planner is designed to be imported by `oracle_api/workflow.py`, but that wiring is not yet done. It does not use an LLM, execute repository code, or write to GitHub.

Before submitting, connect it to the existing LangGraph state and conditional edges, pass only scanned source lines to the evidence verifier, preserve current API response fields, and add workflow tests for budget stops, optional tools, and unsupported evidence.

## Suggested PR sequence

1. Add typed planner state and bounded budget classes.
2. Add plan construction and optional tool routing.
3. Add evidence verification and safe trace output.
4. Wire conditional edges into `oracle_api/workflow.py`.
5. Add tests and document that this is a constrained router, not an autonomous LLM.

Record each completed commit SHA and reviewer note in the team progress record.
