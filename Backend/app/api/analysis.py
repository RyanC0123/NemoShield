import os

from fastapi import APIRouter, HTTPException

from app.agent.analysis_service import AIAnalysisService
from app.defense.risk_mapping import map_risk_level
from app.models.api_schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    AnalysisResult,
    ErrorResponse,
)
from app.storage.event_store import load_security_events
from app.storage.trace_store import record_trace


router = APIRouter(
    prefix="/api",
    tags=["AI Analysis"],
)


def find_security_event(event_id: str):
    events = load_security_events()

    for event in events:
        if event.event_id == event_id:
            return event

    raise HTTPException(
        status_code=404,
        detail="Security event not found",
    )


def analyze(event, operation: str) -> tuple[dict, AnalysisResult, list[dict]]:
    mock_mode = os.getenv("NEMOSHIELD_AI_MOCK_MODE", "false").lower() == "true"
    service = AIAnalysisService(mock_mode=mock_mode)
    result, tool_calls = service.analyze_with_trace(event)
    status = (
        "failed"
        if result["classification"] == "unknown"
        or result["risk_score"] is None
        else "completed"
    )
    analysis = None
    if status == "completed":
        analysis = AnalysisResult(
            summary=result["reason"],
            risk_level=map_risk_level(result["risk_score"]).value,
            recommended_action=result["recommended_action"],
        )

    record_trace(
        operation=operation,
        event_id=event.event_id,
        status=status,
        steps=[
            {"name": "event_lookup", "status": "completed"},
            {
                "name": "mock_analysis" if mock_mode else "nemotron_analysis",
                "status": status,
            },
            *(
                [{"name": "nemotron_read_only_tools", "status": "completed"}]
                if tool_calls
                else []
            ),
        ],
        tool_calls=tool_calls,
        result=(
            result
            if operation == "analyze_v2" or analysis is None
            else analysis.model_dump()
        ),
    )
    if analysis is None:
        raise HTTPException(
            status_code=502,
            detail="AI analysis unavailable or inconclusive",
        )
    return result, analysis, tool_calls


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    summary="Analyze a security event",
    description="Analyze a security event using NVIDIA Nemotron.",
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
def analyze_event(request: AnalyzeRequest):
    event = find_security_event(request.event_id)
    _, analysis, _ = analyze(event, "analyze")
    response = AnalyzeResponse(
        event_id=event.event_id,
        status="completed",
        analysis=analysis,
    )
    return response


@router.post(
    "/analyze/v2",
    summary="Analyze security event using Phase 4 AI service",
)
def analyze_event_v2(request: AnalyzeRequest):
    event = find_security_event(request.event_id)
    result, _, tool_calls = analyze(event, "analyze_v2")
    return {
        "event_id": event.event_id,
        "status": "completed",
        "analysis": result,
        "tool_calls": tool_calls,
    }
