
from app.defense.firewall_safety import FirewallSafetyGuard
from datetime import datetime, timezone
from uuid import uuid4
from typing import Any

from app.defense.recommendation_rules import RecommendedAction


class SimulatedResponseService:
    """
    Generates simulated security response records.

    This service NEVER executes real firewall commands.
    """

    def simulate(
        self,
        action: RecommendedAction,
        event_id: str,
    ) -> dict[str, Any]:
        if not isinstance(action, RecommendedAction):
            raise ValueError("Invalid recommended action")

        FirewallSafetyGuard.validate_action(action)

        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id must be a non-empty string")

        return {
            "response_id": str(uuid4()),
            "event_id": event_id,
            "action": action.value,
            "status": "simulated",
            "executed": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": self._get_message(action),
        }

    @staticmethod
    def _get_message(action: RecommendedAction) -> str:
        messages = {
            RecommendedAction.MONITOR:
                "Monitoring recommended. No action executed.",

            RecommendedAction.INVESTIGATE:
                "Investigation recommended. No action executed.",

            RecommendedAction.SIMULATED_BLOCK:
                "IP block simulated. No firewall changes made.",
        }

        return messages[action]
