
from pathlib import Path
from typing import Any, Callable

from app.agent.analysis_service import AIAnalysisService
from app.defense.decision_pipeline import DecisionPipeline
from app.defense.decision_logging import DecisionLoggingService
from app.models.security_event import SecurityEvent


class SecurityAnalysisPipeline:
    """
    Connects Phase 4 AI analysis with Phase 5 decisions.

    Firewall responses remain simulated; operator-run workflows can update
    the separate Arduino indicator through an injected dispatcher.
    """

    def __init__(
        self,
        analysis_service: AIAnalysisService | None = None,
        log_path: str | Path = "data/decisions.jsonl",
    ):
        self.analysis_service = (
            analysis_service
            if analysis_service is not None
            else AIAnalysisService(mock_mode=True)
        )

        self.decision_pipeline = DecisionPipeline(
            DecisionLoggingService(log_path)
        )

    def process(
        self,
        event: SecurityEvent,
    ) -> dict[str, Any]:
        record, _ = self.process_with_trace(event)
        return record

    def process_with_trace(
        self,
        event: SecurityEvent,
        hardware_dispatcher: Callable[[str], dict[str, Any]] | None = None,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        if not isinstance(event, SecurityEvent):
            raise ValueError(
                "event must be a SecurityEvent"
            )

        # Phase 4: Analyze the event
        analysis, tool_calls = self.analysis_service.analyze_with_trace(event)

        # Convert Pydantic model to JSON-compatible dict
        event_data = event.model_dump(mode="json")

        # Phase 5: Decide, simulate, and log
        record = self.decision_pipeline.process(
            event=event_data,
            analysis=analysis,
            hardware_dispatcher=hardware_dispatcher,
        )
        return record, tool_calls
