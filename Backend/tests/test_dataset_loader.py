
import json

import pytest

from app.storage.dataset_loader import load_synthetic_events


def test_load_dataset():
    events = load_synthetic_events()

    assert len(events) == 16
    assert events[0].event_id == "EVT-0001"


def test_missing_dataset(tmp_path):
    missing_file = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        load_synthetic_events(missing_file)


def test_invalid_json(tmp_path):
    bad_file = tmp_path / "invalid.json"
    bad_file.write_text("{ invalid json", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid JSON"):
        load_synthetic_events(bad_file)


def test_invalid_structure(tmp_path):
    bad_file = tmp_path / "invalid_structure.json"
    bad_file.write_text(
        json.dumps({"events": []}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="JSON array"):
        load_synthetic_events(bad_file)


def test_invalid_event(tmp_path):
    bad_file = tmp_path / "invalid_event.json"
    bad_file.write_text(
        json.dumps([{"event_id": "EVT-BAD"}]),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="index 0"):
        load_synthetic_events(bad_file)

def test_missing_source_ip(tmp_path):
    valid_event = load_synthetic_events()[0].model_dump(
        mode="json"
    )
    valid_event.pop("source_ip")

    path = tmp_path / "missing_field.json"
    path.write_text(
        json.dumps([valid_event]),
        encoding="utf-8"
    )

    with pytest.raises(ValueError) as exc_info:
        load_synthetic_events(path)

    assert "index 0" in str(exc_info.value)
    assert "source_ip" in str(exc_info.value)


def test_invalid_ip_error_message(tmp_path):
    event = load_synthetic_events()[0].model_dump(
        mode="json"
    )
    event["source_ip"] = "not-an-ip"

    path = tmp_path / "invalid_ip.json"
    path.write_text(
        json.dumps([event]),
        encoding="utf-8"
    )

    with pytest.raises(ValueError) as exc_info:
        load_synthetic_events(path)

    assert "index 0" in str(exc_info.value)
    assert "source_ip" in str(exc_info.value)


def test_invalid_event_object(tmp_path):
    path = tmp_path / "not_object.json"
    path.write_text(
        json.dumps(["invalid-event"]),
        encoding="utf-8"
    )

    with pytest.raises(
        ValueError, match="event must be a JSON object"
    ):
        load_synthetic_events(path)


def test_error_in_second_event(tmp_path):
    valid_event = load_synthetic_events()[0].model_dump(
        mode="json"
    )
    invalid_event = valid_event.copy()
    invalid_event["severity"] = 999

    path = tmp_path / "second_event_invalid.json"
    path.write_text(
        json.dumps([valid_event, invalid_event]),
        encoding="utf-8"
    )

    with pytest.raises(ValueError) as exc_info:
        load_synthetic_events(path)

    assert "index 1" in str(exc_info.value)
    assert "severity" in str(exc_info.value)
