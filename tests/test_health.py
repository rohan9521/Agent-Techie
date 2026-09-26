import pytest
from fastapi.testclient import TestClient

from agent_techie.config import Settings
from agent_techie.main import create_app


def test_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "agent-techie"}


def test_frontend_is_served_at_root() -> None:
    client = TestClient(create_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "Engineering workspace" in response.text
    assert "Start a workflow" in response.text
    assert "renderDiagram" in response.text
    assert "Code review" in response.text


def test_status_endpoint_reports_safe_llm_configuration() -> None:
    client = TestClient(create_app())

    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json() == {
        "llm_enabled": False,
        "llm_provider": "disabled",
        "model_name": "",
    }


def test_status_endpoint_reports_configured_openai_model() -> None:
    client = TestClient(
        create_app(
            Settings(
                llm_provider="openai",
                model_name="gpt-test",
                openai_api_key="test-key",
            )
        )
    )

    assert client.get("/api/status").json() == {
        "llm_enabled": True,
        "llm_provider": "openai",
        "model_name": "gpt-test",
    }


def test_openai_configuration_requires_api_key() -> None:
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        create_app(Settings(llm_provider="openai"))


def test_task_endpoint_validates_repository_and_task() -> None:
    client = TestClient(create_app())

    response = client.post("/api/tasks", json={"repository": "bad", "task": ""})

    assert response.status_code == 422


def test_task_endpoint_rejects_whitespace_task() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/tasks", json={"repository": "octo/demo", "task": "   "}
    )

    assert response.status_code == 422


def test_approval_endpoint_resumes_a_paused_workflow() -> None:
    client = TestClient(create_app())
    task_response = client.post(
        "/api/tasks",
        json={
            "repository": "octo/demo",
            "task": "Add a feature",
            "requires_approval": True,
        },
    )
    run_id = task_response.json()["run_id"]

    assert client.get(f"/api/runs/{run_id}").json()["status"] == "waiting_approval"
    events = client.get(f"/api/runs/{run_id}/events").json()
    assert events
    assert all(event["timestamp"] for event in events)

    approval_response = client.post(
        f"/api/runs/{run_id}/approval",
        json={"approved": True},
    )

    assert approval_response.status_code == 202
    assert client.get(f"/api/runs/{run_id}").json()["status"] == "completed"
