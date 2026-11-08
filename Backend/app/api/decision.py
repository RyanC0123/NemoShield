
from typing import Any
import json
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, field_validator

from app.agent.analysis_service import AIAnalysisService
from app.agent.security_analysis_pipeline import SecurityAnalysisPipeline
from app.hardware.alert_service import ArduinoAlertService, get_alert_service
from app.models.security_event import SecurityEvent
from app.storage.decision_store import DECISIONS_PATH, load_decisions
from app.storage.trace_store import record_trace


router = APIRouter(prefix="/api", tags=["Security Decisions"])


class DecisionRequest(BaseModel):
    event: SecurityEvent

    @field_validator("event", mode="before")
    @classmethod
    def validate_event(cls, value):
        if isinstance(value, dict):
            return SecurityEvent.model_validate_json(
                json.dumps(value)
            )

        return value



def get_security_pipeline() -> SecurityAnalysisPipeline:
    mock_mode = os.getenv("NEMOSHIELD_AI_MOCK_MODE", "false").lower() == "true"
    return SecurityAnalysisPipeline(
        analysis_service=AIAnalysisService(mock_mode=mock_mode),
        log_path=DECISIONS_PATH
    )


def get_hardware_service() -> ArduinoAlertService:
    return get_alert_service()



@router.post("/analyze-and-decide")
def analyze_and_decide(
    request: DecisionRequest,
    pipeline: SecurityAnalysisPipeline = Depends(get_security_pipeline),
    hardware_service: ArduinoAlertService = Depends(get_hardware_service),
) -> dict[str, Any]:
    """
    Analyze an event, record the recommendation, and update the Arduino alert.
    """
    event = request.event
    try:
        record, tool_calls = pipeline.process_with_trace(
            event,
            hardware_dispatcher=hardware_service.set_alert,
        )

    except ValueError as exc:
        record_trace(
            operation="analyze_and_decide",
            event_id=event.event_id,
            status="failed",
            steps=[
                {"name": "validation", "status": "completed"},
                {"name": "decision_pipeline", "status": "failed"},
            ],
            error=str(exc),
        )
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    hardware_result = record["decision"]["response"]["hardware"]
    hardware_trace_status = (
        "failed"
        if not hardware_result["ok"]
        else "completed"
        if not hardware_result["simulated"]
        else "simulated"
    )
    record_trace(
        operation="analyze_and_decide",
        event_id=event.event_id,
        status="failed" if not hardware_result["ok"] else "completed",
        steps=[
            {"name": "validation", "status": "completed"},
            {"name": "event_analysis", "status": "completed"},
            *(
                [{"name": "nemotron_read_only_tools", "status": "completed"}]
                if tool_calls
                else []
            ),
            {"name": "policy_decision", "status": "completed"},
            {
                "name": "arduino_alert",
                "status": hardware_trace_status,
            },
            {"name": "audit_log", "status": "completed"},
        ],
        tool_calls=tool_calls,
        result={
            "classification": record["analysis"]["classification"],
            "risk_score": record["analysis"]["risk_score"],
            "action": record["decision"]["action"],
            "executed": record["decision"]["response"]["executed"],
            "hardware": record["decision"]["response"]["hardware"],
        },
        error=hardware_result.get("error"),
    )
    return record


@router.get(
    "/decisions",
    summary="List persisted security decisions",
)
def get_decisions(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    event_id: str | None = None,
):
    decisions = load_decisions()
    if event_id is not None:
        decisions = [
            item for item in decisions
            if item.get("event", {}).get("event_id") == event_id
        ]
    decisions.reverse()
    return {
        "decisions": decisions[offset:offset + limit],
        "total": len(decisions),
        "limit": limit,
        "offset": offset,
    }
