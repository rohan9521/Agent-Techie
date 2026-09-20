# Agent Techie

Agent Techie is a dependency-safe multi-agent software engineering platform. It
turns a repository task into validated requirements, architecture, an implementation
proposal, deterministic test and review reports, and (optionally) a human approval
step. The default runtime is local and network-free; external services are
replaceable interfaces.

## Included phases

* **Agents:** requirements, architect, coder, tester, reviewer, and supervisor.
* **Workflow:** LangGraph `StateGraph` with conditional routing, iteration limits,
  implementation loops, resumable approval state, and validated Pydantic state.
* **Tools:** workspace-root constrained reads/writes/listing and shell commands
  restricted to an allowlist (no shell operators).
* **API:** projects, asynchronous tasks, runs, run events, and approval endpoints.
* **Persistence:** thread-safe in-memory storage by default, plus dependency-free
  PostgreSQL/Redis-compatible adapter boundaries.
* **GitHub:** safe in-memory/no-op service and optional standard-library HTTP adapter.
* **Operations:** JSON logging, optional LangSmith-compatible tracing configuration,
  Docker, Compose, and CI.

## Local setup

Requires Python 3.11+:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
uvicorn agent_techie.main:app --reload
```

`POST /api/tasks` returns `202` and a run ID. Set `requires_approval` to `true` to
pause after review, then call `POST /api/runs/{run_id}/approval`. `GET
/api/runs/{run_id}/events` returns structured lifecycle events. All default task
execution is deterministic and does not call an LLM.

## Quality checks

```bash
pytest
ruff check .
ruff format --check .
mypy src
```

Docker:

```bash
docker compose up --build
```

Secrets belong in environment variables. Configure `LANGSMITH_TRACING` and
`LANGSMITH_API_KEY` only when tracing is desired. Configure a production persistence
adapter and a real GitHub service at the application composition boundary.
