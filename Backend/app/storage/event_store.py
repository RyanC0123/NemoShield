"""Persistence for externally ingested security events."""
import json
import os
import threading
from pathlib import Path

from app.models.security_event import SecurityEvent
from app.storage.dataset_loader import load_synthetic_events


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
INGESTED_EVENTS_PATH = Path(
    os.getenv("NEMOSHIELD_INGESTED_EVENTS_PATH", DATA_DIR / "ingested_events.jsonl")
)
_LOCK = threading.RLock()


class DuplicateEventError(ValueError):
    """Raised when an event ID is reused for different event data."""


def load_ingested_events() -> list[SecurityEvent]:
    if not INGESTED_EVENTS_PATH.exists():
        return []

    events = []
    with _LOCK, INGESTED_EVENTS_PATH.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                events.append(SecurityEvent.model_validate_json(line))
            except ValueError as exc:
                raise ValueError(
                    f"Invalid ingested event at line {line_number}"
                ) from exc
    return events


def load_security_events() -> list[SecurityEvent]:
    """Return seeded events and persisted ingested events."""
    seeded_events = load_synthetic_events()
    ingested_events = load_ingested_events()
    events_by_id = {event.event_id: event for event in seeded_events}

    for event in ingested_events:
        if event.event_id in events_by_id:
            raise ValueError(
                f"Duplicate event ID found in event sources: {event.event_id}"
            )
        events_by_id[event.event_id] = event

    return list(events_by_id.values())


def ingest_security_event(event: SecurityEvent) -> tuple[SecurityEvent, bool]:
    """Append an event once; identical retries are idempotent."""
    if not isinstance(event, SecurityEvent):
        raise ValueError("event must be a validated SecurityEvent")

    event_data = event.model_dump(mode="json")
    with _LOCK:
        for existing in load_security_events():
            if existing.event_id != event.event_id:
                continue
            if existing.model_dump(mode="json") == event_data:
                return existing, False
            raise DuplicateEventError(
                f"Event ID {event.event_id} already exists with different data"
            )

        INGESTED_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with INGESTED_EVENTS_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event_data, ensure_ascii=False) + "\n")
        return event, True
