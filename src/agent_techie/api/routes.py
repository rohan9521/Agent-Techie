import logging
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from agent_techie.persistence import InMemoryPersistence
from agent_techie.schemas.requests import (
    ApprovalRequest,
    EventResponse,
    ProjectRequest,
    ProjectResponse,
    RunResponse,
    TaskRequest,
    TaskResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _dump(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return {key: _dump(item) for key, item in value.model_dump().items()}
    if isinstance(value, dict):
        return {str(key): _dump(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_dump(item) for item in value]
    return value


def _event(
    persistence: InMemoryPersistence, run_id: str, name: str, data: dict[str, object]
) -> None:
    persistence.append_event(
        {
            "run_id": run_id,
            "event": name,
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


def _run_task(run_id: str, request_data: dict[str, object], request: Request) -> None:
    persistence = request.app.state.persistence
    workflow_factory: Callable[[], Any] = request.app.state.workflow_factory
    persistence.save_run(
        {
            "run_id": run_id,
            "status": "running",
            "project_id": request_data.get("project_id"),
        }
    )
    _event(persistence, run_id, "run.started", {})
    try:
        result = workflow_factory().invoke(
            {
                "user_request": request_data["task"],
                "repository": request_data["repository"],
                "execute_implementation": request_data.get(
                    "execute_implementation", True
                ),
                "requires_approval": request_data.get("requires_approval", False),
            }
        )
        dumped = _dump(result)
        status = str(result.get("status", "completed"))
        persistence.save_run(
            {
                "run_id": run_id,
                "status": status,
                "project_id": request_data.get("project_id"),
                "result": dumped,
                "request": request_data,
            }
        )
        _event(
            persistence,
            run_id,
            "run.completed" if status == "completed" else "run.updated",
            dumped,
        )
    except Exception as exc:
        logger.exception("workflow failed", extra={"run_id": run_id})
        persistence.save_run({"run_id": run_id, "status": "failed", "error": str(exc)})
        _event(persistence, run_id, "run.failed", {"error": str(exc)})


@router.post("/projects", response_model=ProjectResponse, status_code=201)
def create_project(payload: ProjectRequest, request: Request) -> ProjectResponse:
    project_id = str(uuid4())
    value = request.app.state.persistence.save_project(
        {"project_id": project_id, **payload.model_dump()}
    )
    return ProjectResponse.model_validate(value)


@router.get("/projects", response_model=list[ProjectResponse])
def list_projects(request: Request) -> list[ProjectResponse]:
    return [
        ProjectResponse.model_validate(p)
        for p in request.app.state.persistence.list_projects()
    ]


@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, request: Request) -> ProjectResponse:
    value = request.app.state.persistence.get_project(project_id)
    if value is None:
        raise HTTPException(status_code=404, detail="project not found")
    return ProjectResponse.model_validate(value)


@router.post("/tasks", response_model=TaskResponse, status_code=202)
def create_task(
    payload: TaskRequest, background_tasks: BackgroundTasks, request: Request
) -> TaskResponse:
    run_id = str(uuid4())
    request_data = payload.model_dump()
    request.app.state.persistence.save_run(
        {
            "run_id": run_id,
            "status": "queued",
            "project_id": payload.project_id,
            "request": request_data,
        }
    )
    _event(request.app.state.persistence, run_id, "run.queued", request_data)
    background_tasks.add_task(_run_task, run_id, request_data, request)
    return TaskResponse(run_id=run_id, status="queued")


@router.post(
    "/projects/{project_id}/tasks", response_model=TaskResponse, status_code=202
)
def create_project_task(
    project_id: str,
    payload: TaskRequest,
    background_tasks: BackgroundTasks,
    request: Request,
) -> TaskResponse:
    project = request.app.state.persistence.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="project not found")
    scoped_payload = payload.model_copy(
        update={"project_id": project_id, "repository": project["repository"]}
    )
    return create_task(scoped_payload, background_tasks, request)


@router.get("/runs", response_model=list[RunResponse])
def list_runs(request: Request, project_id: str | None = None) -> list[RunResponse]:
    return [
        RunResponse.model_validate(r)
        for r in request.app.state.persistence.list_runs(project_id)
    ]


@router.get("/projects/{project_id}/runs", response_model=list[RunResponse])
def list_project_runs(project_id: str, request: Request) -> list[RunResponse]:
    if request.app.state.persistence.get_project(project_id) is None:
        raise HTTPException(status_code=404, detail="project not found")
    return [
        RunResponse.model_validate(run)
        for run in request.app.state.persistence.list_runs(project_id)
    ]


@router.get("/runs/{run_id}", response_model=RunResponse)
def get_run(run_id: str, request: Request) -> RunResponse:
    value = request.app.state.persistence.get_run(run_id)
    if value is None:
        raise HTTPException(status_code=404, detail="run not found")
    return RunResponse.model_validate(value)


@router.get("/projects/{project_id}/runs/{run_id}", response_model=RunResponse)
def get_project_run(project_id: str, run_id: str, request: Request) -> RunResponse:
    value = get_run(run_id, request)
    if value.project_id != project_id:
        raise HTTPException(status_code=404, detail="run not found")
    return value


@router.get("/runs/{run_id}/events", response_model=list[EventResponse])
def list_events(run_id: str, request: Request) -> list[EventResponse]:
    if request.app.state.persistence.get_run(run_id) is None:
        raise HTTPException(status_code=404, detail="run not found")
    return [
        EventResponse.model_validate(e)
        for e in request.app.state.persistence.list_events(run_id)
    ]


@router.get(
    "/events/{run_id}", response_model=list[EventResponse], include_in_schema=False
)
def list_events_alias(run_id: str, request: Request) -> list[EventResponse]:
    return list_events(run_id, request)


@router.post("/runs/{run_id}/approval", response_model=RunResponse, status_code=202)
def approve_run(
    run_id: str,
    payload: ApprovalRequest,
    background_tasks: BackgroundTasks,
    request: Request,
) -> RunResponse:
    run = request.app.state.persistence.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="run not found")
    if run.get("status") != "waiting_approval":
        raise HTTPException(status_code=409, detail="run is not awaiting approval")
    result = dict(run.get("result") or {})
    result["approval"] = payload.approved
    data = dict(run.get("request") or {})
    data["execute_implementation"] = True
    request.app.state.persistence.save_run(
        {**run, "status": "queued", "result": result}
    )
    background_tasks.add_task(_resume_task, run_id, result, data, request)
    return RunResponse(run_id=run_id, status="queued", project_id=run.get("project_id"))


def _resume_task(
    run_id: str,
    state: dict[str, object],
    request_data: dict[str, object],
    request: Request,
) -> None:
    persistence = request.app.state.persistence
    try:
        result = request.app.state.workflow_factory().invoke(
            {
                **state,
                "approval": state.get("approval"),
                "execute_implementation": True,
                "requires_approval": True,
            }
        )
        dumped = _dump(result)
        persistence.save_run(
            {
                **(persistence.get_run(run_id) or {}),
                "status": result.get("status"),
                "result": dumped,
            }
        )
        _event(persistence, run_id, "run.completed", dumped)
    except Exception as exc:
        persistence.save_run(
            {
                **(persistence.get_run(run_id) or {}),
                "status": "failed",
                "error": str(exc),
            }
        )
        _event(persistence, run_id, "run.failed", {"error": str(exc)})
