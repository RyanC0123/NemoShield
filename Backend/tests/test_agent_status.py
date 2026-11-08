from fastapi.testclient import TestClient

import app.api.agent_routes as agent_routes
from app.main import app


def test_agent_status_reports_mock_mode_and_configuration(monkeypatch):
    monkeypatch.setattr(agent_routes, "NVIDIA_API_KEY", "configured-test-key")
    monkeypatch.setenv("NEMOSHIELD_AI_MOCK_MODE", "true")

    with TestClient(app) as client:
        response = client.get("/api/agent/status")

    assert response.status_code == 200
    assert response.json() == {
        "configured": True,
        "mode": "mock",
        "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "test_available": False,
    }


def test_agent_status_does_not_expose_or_require_api_key(monkeypatch):
    monkeypatch.setattr(agent_routes, "NVIDIA_API_KEY", "")
    monkeypatch.delenv("NEMOSHIELD_AI_MOCK_MODE", raising=False)

    with TestClient(app) as client:
        response = client.get("/api/agent/status")

    assert response.status_code == 200
    assert response.json()["configured"] is False
    assert response.json()["mode"] == "nemotron"
    assert response.json()["test_available"] is False


def test_nemotron_connection_test_uses_client_without_returning_model_output(
    monkeypatch,
):
    monkeypatch.setattr(agent_routes, "NVIDIA_API_KEY", "configured-test-key")
    monkeypatch.delenv("NEMOSHIELD_AI_MOCK_MODE", raising=False)
    monkeypatch.setattr(
        agent_routes.NemotronClient,
        "generate_response",
        lambda self, prompt: "NEMOSHIELD_OK",
    )

    with TestClient(app) as client:
        response = client.post("/api/agent/test")

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["latency_ms"] >= 0
    assert "NEMOSHIELD_OK" not in response.text


def test_nemotron_connection_test_fails_explicitly_without_key(monkeypatch):
    monkeypatch.setattr(agent_routes, "NVIDIA_API_KEY", "")

    with TestClient(app) as client:
        response = client.post("/api/agent/test")

    assert response.status_code == 503
