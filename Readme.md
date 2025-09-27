# Planner → Executor Agent (LangGraph)

A project that takes a user question, plans the steps, runs simple tools, and returns a summary. Uses **LangGraph** for a clear planner → executor → finalizer flow. Runs with a rule-based planner by default; LLM planning is optional.

## Why LangGraph (short version)
- Clear, deterministic flow with explicit state.
- Easy to add/replace nodes and tools.
- Simple to test and reason about.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

## Endpoints
- `POST /chat` — run the agent.
- `GET /healthz` — health check.
- `GET /docs` — Swagger UI.

### Example
```bash
curl -X POST http://127.0.0.1:8000/chat   -H "Content-Type: application/json"   -d '{"query":"What were total sales in Q1 and what is 12*(7+1)?"}'
```

## Tools (built-in)
- **sql** — in-memory SQLite with a small `sales` table (SELECT only).
- **calculator** — basic arithmetic; trims a trailing sentence period.
- **weather** — stubbed data for a few cities.

## LLM planning (optional)
```bash
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o-mini
```
If LLM planning fails, it falls back to the rule-based planner.

## Customize
- Add tools in `tools.py` and register them in `TOOLS`.
- Tweak planning in `planner.py` (heuristics or LLM prompt).
- Modify the graph in `graph.py` (nodes/edges).
