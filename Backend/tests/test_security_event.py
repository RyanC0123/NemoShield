
import pytest
from pydantic import ValidationError

from app.models.security_event import SecurityEvent


VALID_EVENT = {
    "event_id": "EVT-0001",
    "timestamp": "2026-11-08T10:30:00Z",
    "source_ip": "192.168.1.10",
    "destination_ip": "192.168.1.20",
    "event_type": "port_scan",
    "severity": "high"
}


def test_valid_security_event():
    event = SecurityEvent.model_validate_json(
        __import__("json").dumps(VALID_EVENT)
    )

    assert event.event_id == "EVT-0001"
    assert str(event.source_ip) == "192.168.1.10"
    assert event.event_type.value == "port_scan"
    assert event.severity.value == "high"


def test_invalid_source_ip():
    data = VALID_EVENT.copy()
    data["source_ip"] = "not-an-ip"

    with pytest.raises(ValidationError):
        SecurityEvent.model_validate_json(
            __import__("json").dumps(data)
        )


def test_missing_required_field():
    data = VALID_EVENT.copy()
    del data["event_id"]

    with pytest.raises(ValidationError):
        SecurityEvent.model_validate_json(
            __import__("json").dumps(data)
        )


def test_invalid_severity():
    data = VALID_EVENT.copy()
    data["severity"] = "extreme"

    with pytest.raises(ValidationError):
        SecurityEvent.model_validate_json(
            __import__("json").dumps(data)
        )


def test_extra_field():
    data = VALID_EVENT.copy()
    data["username"] = "admin"

    with pytest.raises(ValidationError):
        SecurityEvent.model_validate_json(
            __import__("json").dumps(data)
        )

def test_invalid_event_id_format():
    data = VALID_EVENT.copy()
    data["event_id"] = "INVALID-123"

    with pytest.raises(ValidationError):
        SecurityEvent.model_validate_json(
            __import__("json").dumps(data)
        )


def test_empty_event_id():
    data = VALID_EVENT.copy()
    data["event_id"] = "   "

    with pytest.raises(ValidationError):
        SecurityEvent.model_validate_json(
            __import__("json").dumps(data)
        )


def test_timestamp_without_timezone():
    data = VALID_EVENT.copy()
    data["timestamp"] = "2026-01-15T10:00:00"

    with pytest.raises(ValidationError):
        SecurityEvent.model_validate_json(
            __import__("json").dumps(data)
        )


def test_invalid_timestamp_format():
    data = VALID_EVENT.copy()
    data["timestamp"] = "not-a-timestamp"

    with pytest.raises(ValidationError):
        SecurityEvent.model_validate_json(
            __import__("json").dumps(data)
        )


def test_invalid_destination_ip():
    data = VALID_EVENT.copy()
    data["destination_ip"] = "999.999.999.999"

    with pytest.raises(ValidationError):
        SecurityEvent.model_validate_json(
            __import__("json").dumps(data)
        )
