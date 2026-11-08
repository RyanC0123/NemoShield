from fastapi.testclient import TestClient

import app.storage.alert_store as alert_store
from app.main import app


def test_acknowledgment_is_persistent_and_idempotent(monkeypatch, tmp_path):
    monkeypatch.setattr(
        alert_store,
        "ACKNOWLEDGMENTS_PATH",
        tmp_path / "acknowledgments.jsonl",
    )
    alert_id = "ALT-EVT-0003"

    with TestClient(app) as client:
        first = client.post(f"/api/alerts/{alert_id}/acknowledge")
        second = client.post(f"/api/alerts/{alert_id}/acknowledge")
        alerts = client.get("/api/alerts").json()["alerts"]

    assert first.status_code == 200
    assert second.json()["acknowledged_at"] == first.json()["acknowledged_at"]
    assert next(item for item in alerts if item["alert_id"] == alert_id)["status"] == "acknowledged"


def test_acknowledgment_rejects_unknown_alert():
    with TestClient(app) as client:
        response = client.post("/api/alerts/ALT-NOT-REAL/acknowledge")

    assert response.status_code == 404
