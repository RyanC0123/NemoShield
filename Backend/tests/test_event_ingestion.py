from datetime import datetime, timezone

from fastapi.testclient import TestClient

import app.api.events as event_routes
import app.storage.event_store as event_store
from app.main import app


def event_payload():
    return {
        "event_id": "EVT-9001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_ip": "192.0.2.90",
        "destination_ip": "198.51.100.90",
        "event_type": "suspicious_login",
        "severity": "high",
    }


def test_ingestion_requires_configured_bearer_token(monkeypatch, tmp_path):
    monkeypatch.setattr(event_routes, "NEMOSHIELD_INGEST_TOKEN", "")
    monkeypatch.setattr(
        event_store,
        "INGESTED_EVENTS_PATH",
        tmp_path / "events.jsonl",
    )

    with TestClient(app) as client:
        response = client.post("/api/events", json=event_payload())

    assert response.status_code == 503


def test_ingestion_persists_event_and_is_idempotent(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(event_routes, "NEMOSHIELD_INGEST_TOKEN", "test-token")
    monkeypatch.setattr(
        event_store,
        "INGESTED_EVENTS_PATH",
        tmp_path / "events.jsonl",
    )
    headers = {"Authorization": "Bearer test-token"}

    with TestClient(app) as client:
        first = client.post(
            "/api/events",
            json=event_payload(),
            headers=headers,
        )
        retry = client.post(
            "/api/events",
            json=first.json()["event"],
            headers=headers,
        )
        events = client.get(
            "/api/events",
            params={"limit": 100},
        ).json()

    assert first.status_code == 201
    assert first.json()["created"] is True
    assert retry.status_code == 200
    assert retry.json()["created"] is False
    assert events["total"] == 17
    assert sum(item["event_id"] == "EVT-9001" for item in events["events"]) == 1
    with TestClient(app) as client:
        summary = client.get("/api/dashboard/summary").json()
        alerts = client.get("/api/alerts").json()
    assert summary["total_events"] == 17
    assert summary["total_alerts"] == 10
    assert any(alert["event_id"] == "EVT-9001" for alert in alerts["alerts"])


def test_ingested_event_can_be_analyzed_in_mock_mode(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(event_routes, "NEMOSHIELD_INGEST_TOKEN", "test-token")
    monkeypatch.setattr(
        event_store,
        "INGESTED_EVENTS_PATH",
        tmp_path / "events.jsonl",
    )
    monkeypatch.setenv("NEMOSHIELD_AI_MOCK_MODE", "true")
    payload = event_payload()

    with TestClient(app) as client:
        ingestion = client.post(
            "/api/events",
            json=payload,
            headers={"Authorization": "Bearer test-token"},
        )
        analysis = client.post(
            "/api/analyze",
            json={"event_id": payload["event_id"]},
        )

    assert ingestion.status_code == 201
    assert analysis.status_code == 200
    assert analysis.json()["analysis"]["risk_level"] == "high"


def test_ingestion_rejects_reused_id_with_different_event(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setattr(event_routes, "NEMOSHIELD_INGEST_TOKEN", "test-token")
    monkeypatch.setattr(
        event_store,
        "INGESTED_EVENTS_PATH",
        tmp_path / "events.jsonl",
    )
    headers = {"Authorization": "Bearer test-token"}
    original = event_payload()
    changed = {**original, "severity": "critical"}

    with TestClient(app) as client:
        client.post("/api/events", json=original, headers=headers)
        response = client.post("/api/events", json=changed, headers=headers)

    assert response.status_code == 409
