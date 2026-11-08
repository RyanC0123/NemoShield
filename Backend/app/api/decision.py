
from pathlib import Path
from typing import Any
import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.agent.security_analysis_pipeline import SecurityAnalysisPipeline
from app.models.security_event import SecurityEvent


router = APIRouter(
    prefix="/api",
    tags=["Security Decisions"],
)



from pydantic import BaseModel, field_validator
from app.models.security_event import SecurityEvent


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
    """
    Default to Mock AI for safe, reproducible testing.
    """
    return SecurityAnalysisPipeline(
        log_path=Path("data/decisions.jsonl")
    )



@router.post("/analyze-and-decide")
def analyze_and_decide(
    request: DecisionRequest,
    pipeline: SecurityAnalysisPipeline = Depends(get_security_pipeline),
) -> dict[str, Any]:
    """
    Analyze a security event and generate a simulated decision.
    """
    try:
        return pipeline.process(request.event)

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

