
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.decision import get_hardware_service, get_security_pipeline
from app.agent.security_analysis_pipeline import SecurityAnalysisPipeline


@pytest.fixture
def client(tmp_path):
    pipeline = SecurityAnalysisPipeline(
        log_path=tmp_path / "decisions.jsonl"
    )
    class FakeHardware:
        def __init__(self):
            self.commands = []
            self.fail = False

        def set_alert(self, level):
            self.commands.append(level)
            return {
                "ok": not self.fail,
                "command": level,
                "hardware_state": None if self.fail else {
                    "NORMAL": "NORMAL",
                    "WARNING": "WARNING",
                    "CRITICAL": "CRITICAL",
                }[level],
                "simulated": False,
                "error": "No board acknowledgment" if self.fail else None,
            }

    hardware = FakeHardware()

    app.dependency_overrides[get_security_pipeline] = (
        lambda: pipeline
    )
    app.dependency_overrides[get_hardware_service] = lambda: hardware

    with TestClient(app) as test_client:
        test_client.app.state.test_hardware = hardware
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
    "event_type,expected_classification,expected_hardware_level",
    [
        ("normal_traffic", "benign", "NORMAL"),
        ("suspicious_login", "suspicious", "WARNING"),
        ("port_scan", "suspicious", "WARNING"),
        ("brute_force", "malicious", "CRITICAL"),
    ],
)
def test_decision_api_success(
    client,
    event_type,
    expected_classification,
    expected_hardware_level,
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
    assert data["decision"]["response"]["hardware"] == {
        "command": expected_hardware_level,
        "ok": True,
        "simulated": False,
        "state": expected_hardware_level,
        "error": None,
    }
    assert client.app.state.test_hardware.commands == [expected_hardware_level]


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


def test_decision_api_reports_hardware_failure(client):
    client.app.state.test_hardware.fail = True

    response = client.post(
        "/api/analyze-and-decide",
        json=make_payload(),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["decision"]["response"]["hardware"]["ok"] is False
    assert (
        data["decision"]["response"]["hardware"]["error"]
        == "No board acknowledgment"
    )
