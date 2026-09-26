# Agent Techie

Agent Techie is a local-first, multi-agent software-engineering workflow service.
Give it a repository (`owner/name`) and a task. The requirements agent turns the
task into structured requirements, the architect creates a design and plan, and,
when implementation is enabled, coder, tester, and reviewer agents produce and
validate a proposed change. A supervisor routes between phases and can pause for
human approval.

The workflow is deterministic and does not call an LLM by default. The current
coder produces a reviewable change proposal; it does not clone or modify a remote
GitHub repository. The repository field identifies the project being discussed.

## What is included

- **Web dashboard:** create and select projects, start workflows, follow run status,
  inspect structured results and lifecycle events, and approve or deny paused runs.
- **REST API:** project management, standalone and project-scoped task submission,
  run listing/details, event history, and human approval.
- **Workflow agents:** requirements, architecture, implementation proposal, test
  report, review, and supervisor routing.
- **Workspace tools:** root-constrained workspace reads/writes/listing and
  allowlisted shell commands (no shell operators).
- **Runtime:** FastAPI, JSON logging, in-memory persistence by default, optional
  tracing configuration, Docker, Compose, and CI.

## Run locally

Requires Python 3.11 or newer.

```bash
git clone <repository-url>
cd Agent-Techie
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
cp .env.example .env
uvicorn agent_techie.main:app --reload
```

Open **http://127.0.0.1:8000/** for the dashboard. The interactive API reference
is at **http://127.0.0.1:8000/docs**; the alternative ReDoc page is
**http://127.0.0.1:8000/redoc**. The health check is **http://127.0.0.1:8000/health**.

The frontend is served by the FastAPI app, so it needs no separate Node install,
development server, or CORS configuration. It calls the same-origin API and
refreshes run state and events automatically.

## Run with Docker Compose

Docker and the Compose plugin are required.

```bash
docker compose up --build
```

The dashboard and API are available on **http://localhost:8000/** and
**http://localhost:8000/docs**. Compose starts the application, PostgreSQL, and
Redis. The current application composition still uses in-memory persistence;
starting the database services does not by itself switch persistence to them.
Stop the services with `docker compose down`. Persistent database/Redis volumes
remain; use `docker compose down -v` only when you intentionally want to remove
their stored data.

## Configuration

The application reads environment variables and values in `.env`:

| Variable | Default | Purpose |
| --- | --- | --- |
| `ENVIRONMENT` | `development` | Runtime environment label. |
| `API_PREFIX` | `/api` | Prefix for the REST API routes. |
| `LOG_LEVEL` | `INFO` | Logging verbosity. |
| `LLM_PROVIDER` | unset | Reserved provider configuration; no LLM is used by default. |
| `MODEL_NAME` | unset | Reserved model configuration. |
| `WORKSPACE_ROOT` | `.` | Root boundary for workspace tools. |
| `MAX_WORKFLOW_ITERATIONS` | `20` | Maximum supervisor routing iterations. |
| `PERSISTENCE_BACKEND` | `memory` | Persistence selection setting; the current app composition uses in-memory persistence. |
| `DATABASE_URL` | unset | Database adapter configuration boundary. |
| `REDIS_URL` | unset | Redis adapter configuration boundary. |
| `LANGSMITH_TRACING` | `false` | Enable optional LangSmith-compatible tracing. |
| `LANGSMITH_ENDPOINT` | `https://api.smith.langchain.com` | Tracing endpoint. |
| `LANGSMITH_API_KEY` | unset | Tracing credential; keep it secret and configure only when tracing is enabled. |
| `LANGSMITH_PROJECT` | `agent-techie` | Tracing project name. |
| `GITHUB_TOKEN` | unset | Optional GitHub service credential; do not commit credentials. |

See [.env.example](.env.example) for the complete template. PostgreSQL, Redis,
GitHub, and tracing settings do not activate production adapters by themselves;
configure those integrations at the application composition boundary before
relying on them.

## REST API

All JSON API routes use the `/api` prefix by default. The OpenAPI schema is
available at `/openapi.json`; `/docs` lists the documented routes interactively.

### System

| Method and path | What it does |
| --- | --- |
| `GET /health` | Returns `{"status":"ok","service":"agent-techie"}` when the app is responding. |

### Projects

| Method and path | What it does |
| --- | --- |
| `POST /api/projects` | Creates a project. Body: `{"name":"Demo","repository":"octo/demo"}`. Returns `201` and a project ID. |
| `GET /api/projects` | Lists projects. |
| `GET /api/projects/{project_id}` | Gets one project; returns `404` if it does not exist. |

### Tasks and workflow runs

| Method and path | What it does |
| --- | --- |
| `POST /api/tasks` | Queues a standalone workflow and returns `202` with `run_id` and `status`. |
| `POST /api/projects/{project_id}/tasks` | Queues a workflow for a project. The project must exist; its stored repository is used. Returns `404` for an unknown project. |
| `GET /api/runs` | Lists runs. Optional `project_id` query parameter filters the list. |
| `GET /api/projects/{project_id}/runs` | Lists runs for a project; returns `404` if the project does not exist. |
| `GET /api/runs/{run_id}` | Gets run status, result, or error; returns `404` for an unknown run. |
| `GET /api/projects/{project_id}/runs/{run_id}` | Gets a run scoped to a project; returns `404` if the run is missing or belongs to another project. |
| `GET /api/runs/{run_id}/events` | Lists lifecycle events for a run; returns `404` for an unknown run. |

Task body:

```json
{
  "repository": "octo/demo",
  "task": "Add pagination to the projects endpoint",
  "project_id": null,
  "execute_implementation": true,
  "requires_approval": false
}
```

`repository` must be in `owner/name` form and `task` must contain non-whitespace
text. `project_id` is optional. `execute_implementation` defaults to `true`; set it
to `false` for requirements and architecture analysis only. Set
`requires_approval` to `true` to pause an implementation workflow after review.
The task endpoints return a queued run immediately; check its status with the run
endpoints. Statuses include `queued`, `running`, `waiting_approval`, `completed`,
and `failed`.

### Human approval

| Method and path | What it does |
| --- | --- |
| `POST /api/runs/{run_id}/approval` | Resumes a run awaiting approval. Body: `{"approved":true}` continues implementation; `{"approved":false}` denies approval and the run fails. Returns `202`; returns `404` for an unknown run and `409` if the run is not waiting for approval. |

### Example API session

```bash
# Create a project
curl -X POST http://127.0.0.1:8000/api/projects \
  -H 'Content-Type: application/json' \
  -d '{"name":"Demo","repository":"octo/demo"}'

# Start a workflow (replace PROJECT_ID with the returned project_id)
curl -X POST http://127.0.0.1:8000/api/projects/PROJECT_ID/tasks \
  -H 'Content-Type: application/json' \
  -d '{"repository":"octo/demo","task":"Add pagination","execute_implementation":true,"requires_approval":true}'

# Inspect run status/results and events (replace RUN_ID with the returned run_id)
curl http://127.0.0.1:8000/api/runs/RUN_ID
curl http://127.0.0.1:8000/api/runs/RUN_ID/events

# Once status is waiting_approval, approve and resume the workflow
curl -X POST http://127.0.0.1:8000/api/runs/RUN_ID/approval \
  -H 'Content-Type: application/json' \
  -d '{"approved":true}'
```

The `/events/{run_id}` alias is also available but is not included in the OpenAPI
schema; prefer `/api/runs/{run_id}/events`.

## Development and tests

```bash
pytest
ruff check .
ruff format --check .
mypy src
```

The default in-memory store is process-local and is cleared when the app restarts.
Use a production persistence adapter for durable or multi-worker deployments.
