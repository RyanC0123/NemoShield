from datetime import datetime, timezone

from fastapi.testclient import TestClient

import app.api.decision as decision_routes
import app.storage.decision_store as decision_store
import app.storage.trace_store as trace_store
from app.agent.security_analysis_pipeline import SecurityAnalysisPipeline
from app.main import app
from app.api.decision import get_hardware_service, get_security_pipeline


def make_payload():
    return {
        "event": {
            "event_id": "EVT-0001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_ip": "192.0.2.10",
            "destination_ip": "198.51.100.20",
            "event_type": "port_scan",
            "severity": "high",
        }
    }


def test_decision_history_and_trace_are_persisted(monkeypatch, tmp_path):
    decisions_path = tmp_path / "decisions.jsonl"
    traces_path = tmp_path / "traces.jsonl"
    monkeypatch.setattr(decision_store, "DECISIONS_PATH", decisions_path)
    monkeypatch.setattr(decision_routes, "DECISIONS_PATH", decisions_path)
    monkeypatch.setattr(trace_store, "TRACES_PATH", traces_path)
    pipeline = SecurityAnalysisPipeline(log_path=decisions_path)
    class FakeHardware:
        @staticmethod
        def set_alert(level):
            return {
                "ok": True,
                "command": level,
                "hardware_state": level,
                "simulated": True,
            }

    app.dependency_overrides[get_security_pipeline] = lambda: pipeline
    app.dependency_overrides[get_hardware_service] = lambda: FakeHardware()

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/analyze-and-decide",
                json=make_payload(),
            )
            history = client.get(
                "/api/decisions",
                params={"event_id": "EVT-0001"},
            ).json()
            trace_history = client.get(
                "/api/traces",
                params={"event_id": "EVT-0001"},
            ).json()
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert history["total"] == 1
    assert history["decisions"][0]["decision_id"] == response.json()["decision_id"]
    trace = trace_history["traces"][0]
    assert trace["operation"] == "analyze_and_decide"
    assert trace["tool_calls"] == []
    assert trace["result"]["hardware"]["command"] == "WARNING"
    assert trace["steps"][-2]["name"] == "arduino_alert"
    assert trace["steps"][-1]["name"] == "audit_log"


def test_trace_store_filters_by_event_and_operation(monkeypatch, tmp_path):
    monkeypatch.setattr(trace_store, "TRACES_PATH", tmp_path / "traces.jsonl")
    trace_store.record_trace(
        operation="analyze",
        event_id="EVT-0001",
        status="completed",
        steps=[{"name": "nemotron_analysis", "status": "completed"}],
    )
    trace_store.record_trace(
        operation="agent_chat",
        status="completed",
        steps=[{"name": "nemotron_chat", "status": "completed"}],
    )

    traces = trace_store.load_traces(
        event_id="EVT-0001",
        operation="analyze",
    )

    assert len(traces) == 1
    assert traces[0]["event_id"] == "EVT-0001"
