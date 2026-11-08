
from typing import Any

from app.defense.decision_engine import DecisionEngine
from app.defense.simulated_response import SimulatedResponseService
from app.defense.decision_logging import DecisionLoggingService
from app.defense.recommendation_rules import RecommendedAction


class DecisionPipeline:
    """
    Orchestrates deterministic security decisions,
    simulated responses, and audit logging.
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
