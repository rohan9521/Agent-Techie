import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent_techie.config import Settings
from agent_techie.main import create_app


def _create_default_app() -> FastAPI:
    return create_app(Settings(_env_file=None, llm_provider="disabled"))


def test_health_endpoint() -> None:
    client = TestClient(_create_default_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "agent-techie"}


def test_frontend_is_served_at_root() -> None:
    client = TestClient(_create_default_app())

    response = client.get("/")

    assert response.status_code == 200
    assert "Engineering workspace" in response.text
    assert "Start a workflow" in response.text
    assert "renderDiagram" in response.text
    assert "Code review" in response.text
    assert "Generated code" in response.text
    assert "first file expanded below" in response.text
    assert 'id="workspace-view"' in response.text
    assert 'id="workflow-view" class="hidden workflow-page"' in response.text
    assert "Workflow status" in response.text
    assert 'id="app-tabs" class="app-tabs" role="tablist"' in response.text
    assert "data-workspace-tab>Engineering workspace</button>" in response.text
    assert 'role="tab" aria-selected="${state.runId === tab.run_id}"' in response.text
    assert 'href="#workflow/${encodeURIComponent(run.run_id)}"' in response.text
    assert 'target="_blank"' not in response.text


def test_status_endpoint_reports_safe_llm_configuration() -> None:
    client = TestClient(_create_default_app())

    response = client.get("/api/status")

    assert response.status_code == 200
    assert response.json() == {
        "llm_enabled": False,
        "llm_provider": "disabled",
        "model_name": "",
    }


@pytest.mark.parametrize(
    ("provider", "model_name", "api_key_field"),
    [
        ("openai", "gpt-test", "openai_api_key"),
        ("gemini", "gemini-test", "gemini_api_key"),
        ("anthropic", "claude-test", "anthropic_api_key"),
    ],
)
def test_status_endpoint_reports_configured_cloud_model(
    provider: str, model_name: str, api_key_field: str
) -> None:
    settings = Settings(
        llm_provider=provider,
        model_name=model_name,
        **{api_key_field: "test-key"},
    )
    client = TestClient(create_app(settings))

    assert client.get("/api/status").json() == {
        "llm_enabled": True,
        "llm_provider": provider,
        "model_name": model_name,
    }


def test_status_endpoint_reports_configured_ollama_model() -> None:
    client = TestClient(
        create_app(
            Settings(
                llm_provider="ollama",
                model_name="llama3.2",
                ollama_base_url="http://localhost:11434",
            )
        )
    )

    assert client.get("/api/status").json() == {
        "llm_enabled": True,
        "llm_provider": "ollama",
        "model_name": "llama3.2",
    }


@pytest.mark.parametrize(
    ("provider", "key_name"),
    [
        ("openai", "OPENAI_API_KEY"),
        ("gemini", "GEMINI_API_KEY"),
        ("anthropic", "ANTHROPIC_API_KEY"),
    ],
)
def test_cloud_configuration_requires_api_key(provider: str, key_name: str) -> None:
    with pytest.raises(ValueError, match=key_name):
        create_app(Settings(llm_provider=provider))


def test_status_endpoint_reports_disabled_provider() -> None:
    client = TestClient(create_app(Settings(llm_provider="disabled")))

    assert client.get("/api/status").json() == {
        "llm_enabled": False,
        "llm_provider": "disabled",
        "model_name": "",
    }


def test_task_endpoint_validates_repository_and_task() -> None:
    client = TestClient(_create_default_app())

    response = client.post("/api/tasks", json={"repository": "bad", "task": ""})

    assert response.status_code == 422


def test_task_endpoint_rejects_whitespace_task() -> None:
    client = TestClient(_create_default_app())

    response = client.post(
        "/api/tasks", json={"repository": "octo/demo", "task": "   "}
    )

    assert response.status_code == 422


def test_approval_endpoint_resumes_a_paused_workflow() -> None:
    client = TestClient(_create_default_app())
    task_response = client.post(
        "/api/tasks",
        json={
            "repository": "octo/demo",
            "task": "Add a feature",
            "requires_approval": True,
        },
    )
    run_id = task_response.json()["run_id"]

    run_response = client.get(f"/api/runs/{run_id}").json()
    assert run_response["status"] == "waiting_approval"
    assert run_response["request"]["task"] == "Add a feature"
    assert run_response["request"]["repository"] == "octo/demo"
    events = client.get(f"/api/runs/{run_id}/events").json()
    assert events
    assert all(event["timestamp"] for event in events)

    approval_response = client.post(
        f"/api/runs/{run_id}/approval",
        json={"approved": True},
    )

    assert approval_response.status_code == 202
    assert client.get(f"/api/runs/{run_id}").json()["status"] == "completed"
