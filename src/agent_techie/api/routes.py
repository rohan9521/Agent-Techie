from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks

from agent_techie.graph.workflow import build_workflow
from agent_techie.schemas.requests import TaskRequest, TaskResponse

router = APIRouter()
_runs: dict[str, dict[str, object]] = {}


def _run_task(run_id: str, request: TaskRequest) -> None:
    try:
        result = build_workflow().invoke(
            {"user_request": request.task, "repository": request.repository}
        )
        _runs[run_id] = {"run_id": run_id, "status": result["status"], "result": result}
    except Exception as exc:
        _runs[run_id] = {"run_id": run_id, "status": "failed", "error": str(exc)}


@router.post("/tasks", response_model=TaskResponse, status_code=202)
def create_task(
    request: TaskRequest, background_tasks: BackgroundTasks
) -> TaskResponse:
    run_id = str(uuid4())
    _runs[run_id] = {"run_id": run_id, "status": "queued"}
    background_tasks.add_task(_run_task, run_id, request)
    return TaskResponse(run_id=run_id, status="queued")
