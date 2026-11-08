"""Persistent alert acknowledgment records."""
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
ACKNOWLEDGMENTS_PATH = Path(
    os.getenv("NEMOSHIELD_ACKNOWLEDGMENTS_PATH", DATA_DIR / "acknowledgments.jsonl")
)
_LOCK = threading.RLock()


def load_acknowledgments() -> dict[str, dict[str, Any]]:
    if not ACKNOWLEDGMENTS_PATH.exists():
        return {}

    records: dict[str, dict[str, Any]] = {}
    with _LOCK, ACKNOWLEDGMENTS_PATH.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                alert_id = record["alert_id"]
                acknowledged_at = record["acknowledged_at"]
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                raise ValueError(
                    f"Invalid alert acknowledgment at line {line_number}"
                ) from exc
            records[alert_id] = {
                "alert_id": alert_id,
                "acknowledged_at": acknowledged_at,
            }
    return records


def acknowledge_alert(alert_id: str) -> dict[str, Any]:
    with _LOCK:
        records = load_acknowledgments()
        if alert_id in records:
            return records[alert_id]

        record = {
            "alert_id": alert_id,
            "acknowledged_at": datetime.now(timezone.utc).isoformat(),
        }
        ACKNOWLEDGMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with ACKNOWLEDGMENTS_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(record) + "\n")
        return record
