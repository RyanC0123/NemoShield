
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.decision import get_security_pipeline
from app.agent.security_analysis_pipeline import SecurityAnalysisPipeline


@pytest.fixture
def client(tmp_path):
    pipeline = SecurityAnalysisPipeline(
        log_path=tmp_path / "decisions.jsonl"
    )

    app.dependency_overrides[get_security_pipeline] = (
        lambda: pipeline
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def make_payload(event_type="brute_force"):
    return {
        "event": {
            "event_id": "EVT-0001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_ip": "192.0.2.10",
            "destination_ip": "10.0.0.5",
            "event_type": event_type,
            "severity": "high",
        }
    }


@pytest.mark.parametrize(
    "event_type,expected_classification",
    [
        ("normal_traffic", "benign"),
        ("suspicious_login", "suspicious"),
        ("port_scan", "suspicious"),
        ("brute_force", "malicious"),
    ],
)
def test_decision_api_success(
    client,
    event_type,
    expected_classification,
):
    response = client.post(
        "/api/analyze-and-decide",
        json=make_payload(event_type),
    )

    assert response.status_code == 200, response.json()

    data = response.json()

    assert data["analysis"]["classification"] == expected_classification
    assert data["decision"]["classification"] == expected_classification

    assert data["decision"]["action"] in {
        "monitor",
        "investigate",
        "simulated_block",
    }

    assert data["decision"]["response"]["executed"] is False
    assert data["decision"]["response"]["status"] == "simulated"


def test_decision_api_rejects_invalid_event(client):
    payload = make_payload()
    payload["event"]["event_id"] = "INVALID-ID"

    response = client.post(
        "/api/analyze-and-decide",
        json=payload,
    )

    assert response.status_code == 422


def test_decision_api_rejects_missing_event(client):
    response = client.post(
        "/api/analyze-and-decide",
        json={},
    )

    assert response.status_code == 422
