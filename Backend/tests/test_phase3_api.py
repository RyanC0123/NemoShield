
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_get_events_success():
    response = client.get("/api/events")

    assert response.status_code == 200

    data = response.json()

    assert "events" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data

    assert isinstance(data["events"], list)
    assert data["total"] == 16
    assert data["limit"] == 50
    assert data["offset"] == 0


def test_get_events_filter_by_severity():
    response = client.get(
        "/api/events",
        params={"severity": "high"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 5
    assert len(data["events"]) == 5

    for event in data["events"]:
        assert event["severity"] == "high"


def test_get_events_pagination():
    # Get first page
    page1 = client.get(
        "/api/events",
        params={
            "limit": 2,
            "offset": 0,
            "severity": "high",
        },
    )

    # Get second page
    page2 = client.get(
        "/api/events",
        params={
            "limit": 2,
            "offset": 2,
            "severity": "high",
        },
    )

    assert page1.status_code == 200
    assert page2.status_code == 200

    data1 = page1.json()
    data2 = page2.json()

    assert data1["total"] == 5
    assert data2["total"] == 5

    assert len(data1["events"]) == 2
    assert len(data2["events"]) == 2

    assert data1["limit"] == 2
    assert data2["limit"] == 2

    assert data1["offset"] == 0
    assert data2["offset"] == 2

    # Verify pages contain different events
    ids1 = {event["event_id"] for event in data1["events"]}
    ids2 = {event["event_id"] for event in data2["events"]}

    assert ids1.isdisjoint(ids2)


def test_get_event_by_id_success():
    response = client.get("/api/events/EVT-0011")

    assert response.status_code == 200

    data = response.json()

    assert data["event_id"] == "EVT-0011"
    assert data["event_type"] == "port_scan"
    assert data["severity"] == "high"

    assert "timestamp" in data
    assert "source_ip" in data
    assert "destination_ip" in data


def test_get_event_by_id_not_found():
    response = client.get("/api/events/EVT-9999")

    assert response.status_code == 404

    data = response.json()

    assert data == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Security event not found",
        }
    }


def test_analyze_event_success(monkeypatch):
    traces = []

    def mock_analyze_with_trace(self, event):
        assert event.event_id == "EVT-0011"
        return (
            {
                "classification": "suspicious",
                "risk_score": 65,
                "reason": "Potential port scanning detected.",
                "recommended_action": "Review firewall logs.",
            },
            [
                {
                    "name": "lookup_related_events",
                    "arguments": {"event_id": "EVT-0011"},
                    "result": {"event_count": 1, "event_ids": ["EVT-0007"]},
                    "status": "completed",
                }
            ],
        )

    monkeypatch.setattr(
        "app.api.analysis.AIAnalysisService.analyze_with_trace",
        mock_analyze_with_trace,
    )
    monkeypatch.setattr(
        "app.api.analysis.record_trace",
        lambda **trace: traces.append(trace),
    )

    response = client.post(
        "/api/analyze",
        json={"event_id": "EVT-0011"},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["event_id"] == "EVT-0011"
    assert data["status"] == "completed"

    assert data["analysis"] == {
        "summary": "Potential port scanning detected.",
        "risk_level": "high",
        "recommended_action": "Review firewall logs.",
    }
    assert traces[0]["tool_calls"][0]["name"] == "lookup_related_events"
    assert traces[0]["result"]["summary"] == "Potential port scanning detected."


def test_analyze_event_not_found(monkeypatch):
    def fail_if_ai_called(self, event):
        raise AssertionError(
            "Nemotron should not be called for missing events"
        )

    monkeypatch.setattr(
        "app.api.analysis.AIAnalysisService.analyze_with_trace",
        fail_if_ai_called,
    )

    response = client.post(
        "/api/analyze",
        json={"event_id": "EVT-9999"},
    )

    assert response.status_code == 404

    assert response.json() == {
        "error": {
            "code": "NOT_FOUND",
            "message": "Security event not found",
        }
    }


def test_analyze_event_invalid_id():
    response = client.post(
        "/api/analyze",
        json={"event_id": "INVALID-ID"},
    )

    assert response.status_code == 422

    assert response.json() == {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
        }
    }


def test_analyze_event_invalid_ai_response(monkeypatch):
    def mock_analyze_with_trace(self, event):
        return (
            {
                "classification": "unknown",
                "risk_score": None,
                "reason": "AI returned an invalid response.",
                "recommended_action": "Flag for manual review and retain event logs.",
            },
            [],
        )

    monkeypatch.setattr(
        "app.api.analysis.AIAnalysisService.analyze_with_trace",
        mock_analyze_with_trace,
    )

    response = client.post(
        "/api/analyze",
        json={"event_id": "EVT-0011"},
    )

    assert response.status_code == 502

    assert response.json() == {
        "error": {
            "code": "BAD_GATEWAY",
            "message": "AI analysis unavailable or inconclusive",
        }
    }


def test_get_alerts_success():
    response = client.get("/api/alerts")

    assert response.status_code == 200

    data = response.json()

    assert "alerts" in data
    assert "total" in data

    assert data["total"] == 9
    assert len(data["alerts"]) == 9

    for alert in data["alerts"]:
        assert alert["severity"] in ("high", "critical")
        assert alert["status"] == "open"

        assert alert["alert_id"] == (
            f"ALT-{alert['event_id']}"
        )

        assert isinstance(alert["message"], str)
        assert len(alert["message"]) > 0


def test_dashboard_summary_success():
    response = client.get("/api/dashboard/summary")

    assert response.status_code == 200

    data = response.json()

    assert data["total_events"] == 16
    assert data["total_alerts"] == 9

    assert data["severity_counts"] == {
        "low": 4,
        "medium": 3,
        "high": 5,
        "critical": 4,
    }

    # Total events must match severity counts
    assert sum(data["severity_counts"].values()) == data["total_events"]

    # Total alerts must match high + critical events
    assert data["total_alerts"] == (
        data["severity_counts"]["high"]
        + data["severity_counts"]["critical"]
    )

    # Dashboard count must match Alerts API
    alerts_response = client.get("/api/alerts")

    assert alerts_response.status_code == 200
    assert data["total_alerts"] == alerts_response.json()["total"]
