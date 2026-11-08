
import json
from datetime import datetime, timezone

import pytest

from app.agent.analysis_service import AIAnalysisService
from app.agent.security_analysis_pipeline import SecurityAnalysisPipeline
from app.models.security_event import SecurityEvent


EventType = SecurityEvent.model_fields["event_type"].annotation
Severity = SecurityEvent.model_fields["severity"].annotation


def make_event(event_type=EventType.BRUTE_FORCE):
    return SecurityEvent(
        event_id="EVT-0001",
        timestamp=datetime.now(timezone.utc),
        source_ip="192.0.2.10",
        destination_ip="10.0.0.5",
        event_type=event_type,
        severity=Severity.HIGH,
    )


@pytest.fixture
def pipeline(tmp_path):
    return SecurityAnalysisPipeline(
        analysis_service=AIAnalysisService(mock_mode=True),
        log_path=tmp_path / "decisions.jsonl",
    )


@pytest.mark.parametrize(
    "event_type,expected_classification",
    [
        (EventType.NORMAL_TRAFFIC, "benign"),
        (EventType.SUSPICIOUS_LOGIN, "suspicious"),
        (EventType.PORT_SCAN, "suspicious"),
        (EventType.BRUTE_FORCE, "malicious"),
    ],
)
def test_phase4_to_phase5_integration(
    pipeline,
    event_type,
    expected_classification,
):
    event = make_event(event_type)

    result = pipeline.process(event)

    assert result["event"]["event_id"] == event.event_id

    assert (
        result["analysis"]["classification"]
        == expected_classification
    )

    assert (
        result["decision"]["classification"]
        == expected_classification
    )

    assert result["decision"]["action"] in {
        "monitor",
        "investigate",
        "simulated_block",
    }

    response = result["decision"]["response"]

    assert response["executed"] is False
    assert response["status"] == "simulated"


def test_integration_writes_audit_log(pipeline):
    event = make_event()

    result = pipeline.process(event)

    log_path = pipeline.decision_pipeline.logging_service.log_path

    assert log_path.exists()

    lines = log_path.read_text(
        encoding="utf-8"
    ).splitlines()

    assert len(lines) == 1

    stored = json.loads(lines[0])

    assert stored == result


def test_integration_repeated_decisions_are_consistent(pipeline):
    event = make_event()

    first = pipeline.process(event)
    second = pipeline.process(event)

    assert first["analysis"] == second["analysis"]

    for field in ("classification", "risk_level", "action"):
        assert first["decision"][field] == second["decision"][field]

    assert first["decision"]["response"]["executed"] is False
    assert second["decision"]["response"]["executed"] is False


def test_invalid_event_rejected(pipeline):
    with pytest.raises(ValueError):
        pipeline.process({"event_id": "invalid"})
