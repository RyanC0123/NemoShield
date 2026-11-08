

from datetime import datetime, timezone

from app.agent.analysis_service import AIAnalysisService
from app.models.security_event import SecurityEvent


EventType = SecurityEvent.model_fields["event_type"].annotation
Severity = SecurityEvent.model_fields["severity"].annotation


def test_build_ai_input():
    event = SecurityEvent(
        event_id="EVT-0001",
        timestamp=datetime.now(timezone.utc),
        source_ip="192.168.1.100",
        destination_ip="10.0.0.5",
        event_type=EventType.BRUTE_FORCE,
        severity=Severity.HIGH,
    )

    service = AIAnalysisService()

    result = service.build_ai_input(event)

    assert "event" in result
    assert result["event"]["event_id"] == "EVT-0001"
    assert result["event"]["source_ip"] == "192.168.1.100"
    assert result["event"]["destination_ip"] == "10.0.0.5"
    assert result["event"]["event_type"] == "brute_force"
    assert result["event"]["severity"] == "high"
    assert isinstance(result["event"]["timestamp"], str)

    print("AI Input Format Test Passed!")
