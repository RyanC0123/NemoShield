"""Persistent, data-minimized investigation traces."""
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


DATA_DIR = Path(__file__).resolve().parents[2] / "data"
TRACES_PATH = Path(
    os.getenv("NEMOSHIELD_TRACES_PATH", DATA_DIR / "investigation_traces.jsonl")
)
_LOCK = threading.RLock()


def record_trace(
    *,
    operation: str,
    status: str,
    steps: list[dict[str, Any]],
    event_id: str | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    trace = {
        "trace_id": str(uuid4()),
        "operation": operation,
        "event_id": event_id,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "steps": steps,
        "tool_calls": tool_calls or [],
    }
    if result is not None:
        trace["result"] = result
    if error is not None:
        trace["error"] = error

    with _LOCK:
        TRACES_PATH.parent.mkdir(parents=True, exist_ok=True)
        with TRACES_PATH.open("a", encoding="utf-8") as file:
            file.write(json.dumps(trace, ensure_ascii=False) + "\n")
    return trace


def load_traces(
    event_id: str | None = None,
    operation: str | None = None,
) -> list[dict[str, Any]]:
    if not TRACES_PATH.exists():
        return []

    traces = []
    with _LOCK, TRACES_PATH.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue
            try:
                trace = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid investigation trace at line {line_number}"
                ) from exc
            if not isinstance(trace, dict):
                raise ValueError(
                    f"Invalid investigation trace at line {line_number}"
                )
            if event_id is not None and trace.get("event_id") != event_id:
                continue
            if operation is not None and trace.get("operation") != operation:
                continue
            traces.append(trace)
    return list(reversed(traces))
