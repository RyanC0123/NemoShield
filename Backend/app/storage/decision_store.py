"""Read-only access to the persisted decision audit log."""
import json
import os
import threading
from pathlib import Path
from typing import Any


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DECISIONS_PATH = Path(
    os.getenv("NEMOSHIELD_DECISIONS_PATH", DATA_DIR / "decisions.jsonl")
)
_LOCK = threading.RLock()


def load_decisions() -> list[dict[str, Any]]:
    if not DECISIONS_PATH.exists():
        return []

    decisions = []
    with _LOCK, DECISIONS_PATH.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid decision record at line {line_number}"
                ) from exc
            if not isinstance(record, dict):
                raise ValueError(
                    f"Invalid decision record at line {line_number}"
                )
            decisions.append(record)
    return decisions
