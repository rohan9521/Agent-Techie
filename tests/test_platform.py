from pathlib import Path

import pytest

from agent_techie.graph.workflow import build_workflow
from agent_techie.main import create_app
from agent_techie.persistence import InMemoryPersistence
from agent_techie.tools.workspace import ToolSecurityError, WorkspaceTools


def test_full_workflow_can_pause_and_resume_for_approval() -> None:
    paused = build_workflow().invoke(
        {
            "user_request": "Add search",
            "repository": "octo/demo",
            "execute_implementation": True,
            "requires_approval": True,
        }
    )
    assert paused["status"] == "waiting_approval"
    resumed = build_workflow().invoke({**paused, "approval": True})
    assert resumed["status"] == "completed"
    assert resumed["review_report"].approved is True


def test_full_workflow_executes_all_implementation_phases() -> None:
    result = build_workflow().invoke(
        {
            "user_request": "Add search",
            "repository": "octo/demo",
            "execute_implementation": True,
        }
    )

    assert result["status"] == "completed"
    assert result["code_change"].changes
    assert result["test_report"].passed is True
    assert result["review_report"].approved is True


def test_workspace_tools_reject_escape_and_shell_operators(tmp_path: Path) -> None:
    tools = WorkspaceTools(tmp_path)
    tools.write_file("notes.txt", "safe")
    assert tools.read_file("notes.txt") == "safe"
    with pytest.raises(ToolSecurityError):
        tools.read_file("../outside.txt")
    with pytest.raises(ToolSecurityError):
        tools.run_command("pytest; echo unsafe")


def test_memory_persistence_keeps_runs_and_events_isolated() -> None:
    persistence = InMemoryPersistence()
    persistence.save_run({"run_id": "one", "status": "queued"})
    persistence.append_event({"run_id": "one", "event": "queued"})
    assert persistence.get_run("one") == {"run_id": "one", "status": "queued"}
    assert persistence.list_events("one")[0]["event"] == "queued"
    assert persistence.list_events("two") == []


def test_project_scoped_routes_create_and_read_runs() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(create_app())
    project = client.post(
        "/api/projects",
        json={"name": "Demo", "repository": "octo/demo"},
    )
    assert project.status_code == 201
    project_id = project.json()["project_id"]

    task = client.post(
        f"/api/projects/{project_id}/tasks",
        json={"repository": "ignored/value", "task": "Add search"},
    )
    assert task.status_code == 202
    run_id = task.json()["run_id"]
    run = client.get(f"/api/projects/{project_id}/runs/{run_id}")
    assert run.status_code == 200
    assert run.json()["project_id"] == project_id
