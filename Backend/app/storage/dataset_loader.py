
import json
import hashlib
from collections import Counter

from pathlib import Path

from pydantic import ValidationError

from app.models.security_event import SecurityEvent


DATASET_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "synthetic_events_v1.json"
)


def load_synthetic_events(
    file_path: str | Path | None = None,
) -> list[SecurityEvent]:
    path = Path(file_path) if file_path is not None else DATASET_PATH

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Dataset file not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON dataset: {exc}"
        ) from exc

    if not isinstance(data, list):
        raise ValueError("Dataset must be a JSON array.")

    
    events = []

    for index, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(
                f"Invalid security event at index {index}: "
                "event must be a JSON object"
            )

        try:
            event = SecurityEvent.model_validate_json(
                json.dumps(item)
            )

        except ValidationError as exc:
            error_messages = []

            for error in exc.errors():
                field = ".".join(
                    str(part) for part in error["loc"]
                ) or "event"

                message = error["msg"]

                error_messages.append(
                    f"{field}: {message}"
                )

            details = "; ".join(error_messages)

            raise ValueError(
                f"Invalid security event at index {index}: "
                f"{details}"
            ) from exc

        events.append(event)

    return events


def verify_dataset_integrity(
    file_path: str | Path | None = None,
    manifest_path: str | Path | None = None,
) -> bool:
    dataset = (
        Path(file_path) if file_path is not None
        else DATASET_PATH
    )

    manifest_file = (
        Path(manifest_path) if manifest_path is not None
        else DATASET_PATH.with_suffix(".manifest.json")
    )

    try:
        with manifest_file.open("r", encoding="utf-8") as file:
            manifest = json.load(file)
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Dataset manifest not found: {manifest_file}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid dataset manifest JSON: {exc}"
        ) from exc

    if not isinstance(manifest, dict):
        raise ValueError("Dataset manifest must be a JSON object")

    if manifest.get("dataset_version") != "1.0.0":
        raise ValueError("Unsupported dataset version")

    if manifest.get("dataset_file") != dataset.name:
        raise ValueError("Dataset filename mismatch")

    raw = dataset.read_bytes()
    actual_hash = hashlib.sha256(raw).hexdigest()

    if actual_hash != manifest.get("sha256"):
        raise ValueError("Dataset SHA-256 checksum mismatch")

    events = load_synthetic_events(dataset)

    if len(events) != manifest.get("expected_event_count"):
        raise ValueError("Dataset event count mismatch")

    ids = [event.event_id for event in events]

    if len(set(ids)) != len(ids):
        raise ValueError("Dataset contains duplicate event IDs")

    if ids != manifest.get("expected_event_ids"):
        raise ValueError("Dataset event IDs mismatch")

    actual_types = dict(sorted(Counter(
        event.event_type.value for event in events
    ).items()))

    if actual_types != manifest.get("expected_event_types"):
        raise ValueError("Dataset event type counts mismatch")

    return True

  