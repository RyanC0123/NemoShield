
from typing import Any, Callable

from app.defense.decision_engine import DecisionEngine
from app.defense.simulated_response import SimulatedResponseService
from app.defense.decision_logging import DecisionLoggingService
from app.defense.recommendation_rules import RecommendedAction


class DecisionPipeline:
    """
    Orchestrates deterministic decisions, optional Arduino alerts,
    simulated firewall responses, and audit logging.
    """

    def __init__(
        self,
        logging_service: DecisionLoggingService,
    ):
        self.engine = DecisionEngine()
        self.response_service = SimulatedResponseService()
        self.logging_service = logging_service

    def process(
        self,
        event: dict[str, Any],
        analysis: dict[str, Any],
        hardware_dispatcher: Callable[[str], dict[str, Any]] | None = None,
    ) -> dict[str, Any]:

        if not isinstance(event, dict):
            raise ValueError("event must be a dictionary")

        if not isinstance(analysis, dict):
            raise ValueError("analysis must be a dictionary")

        event_id = event.get("event_id")

        if not isinstance(event_id, str) or not event_id.strip():
            raise ValueError("event_id must be a non-empty string")

        decision = self.engine.decide(analysis)

        response = self.response_service.simulate(
            RecommendedAction(decision["action"]),
            event_id,
        )
        if hardware_dispatcher is not None:
            hardware_level = {
                RecommendedAction.MONITOR: "NORMAL",
                RecommendedAction.INVESTIGATE: "WARNING",
                RecommendedAction.SIMULATED_BLOCK: "CRITICAL",
            }[RecommendedAction(decision["action"])]
            hardware_result = hardware_dispatcher(hardware_level)
            response["hardware"] = {
                "command": hardware_level,
                "ok": hardware_result["ok"],
                "simulated": hardware_result["simulated"],
                "state": hardware_result.get("hardware_state"),
                "error": hardware_result.get("error"),
            }

        decision_record = {
            **decision,
            "response": response,
        }

        log_record = self.logging_service.log_decision(
            event=event,
            analysis=analysis,
            decision=decision_record,
        )

        return log_record
