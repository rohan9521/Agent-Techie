from fastapi.testclient import TestClient

from agent_techie.main import create_app


def test_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "agent-techie"}


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
