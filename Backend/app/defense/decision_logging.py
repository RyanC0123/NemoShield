
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


class DecisionLoggingService:
    """
    Stores security decision records as JSONL.

    This service only writes audit logs.
    It never performs firewall operations.
    """

    def __init__(self, log_path: str | Path):
        self.log_path = Path(log_path)

    def log_decision(
        self,
        event: dict[str, Any],
        analysis: dict[str, Any],
        decision: dict[str, Any],
    ) -> dict[str, Any]:

        if not isinstance(event, dict):
            raise ValueError("event must be a dictionary")

        if not isinstance(analysis, dict):
            raise ValueError("analysis must be a dictionary")

        if not isinstance(decision, dict):
            raise ValueError("decision must be a dictionary")

        record = {
            "decision_id": str(uuid4()),
            "event": event,
            "analysis": analysis,
            "decision": decision,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.log_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )

        return record
