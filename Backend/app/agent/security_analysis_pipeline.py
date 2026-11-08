
from pathlib import Path
from typing import Any

from app.agent.analysis_service import AIAnalysisService
from app.defense.decision_pipeline import DecisionPipeline
from app.defense.decision_logging import DecisionLoggingService
from app.models.security_event import SecurityEvent


class SecurityAnalysisPipeline:
    """
    Connects Phase 4 AI analysis with Phase 5 decisions.

    All security responses remain simulation-only.
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

        if not isinstance(event, SecurityEvent):
            raise ValueError(
                "event must be a SecurityEvent"
            )

        # Phase 4: Analyze the event
        analysis = self.analysis_service.analyze(event)

        # Convert Pydantic model to JSON-compatible dict
        event_data = event.model_dump(mode="json")

        # Phase 5: Decide, simulate, and log
        return self.decision_pipeline.process(
            event=event_data,
            analysis=analysis,
        )
