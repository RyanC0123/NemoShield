
from pydantic import BaseModel, Field

from app.models.security_event import SecurityEvent


class EventListResponse(BaseModel):
    events: list[SecurityEvent]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)


class AnalyzeRequest(BaseModel):
    event_id: str = Field(
        min_length=1,
        pattern=r"^EVT-[0-9]{4}$"
    )


from typing import Literal


class AnalysisResult(BaseModel):
    summary: str = Field(min_length=1)
    risk_level: Literal["low", "medium", "high", "critical"]
    recommended_action: str = Field(min_length=1)


class AnalyzeResponse(BaseModel):
    event_id: str
    status: Literal["completed"]
    analysis: AnalysisResult


class SecurityAlert(BaseModel):
    alert_id: str
    event_id: str
    severity: str
    message: str
    status: Literal["open"] = "open"


class AlertListResponse(BaseModel):
    alerts: list[SecurityAlert]
    total: int = Field(ge=0)


class SeverityCounts(BaseModel):
    low: int = Field(ge=0)
    medium: int = Field(ge=0)
    high: int = Field(ge=0)
    critical: int = Field(ge=0)


class DashboardSummaryResponse(BaseModel):
    total_events: int = Field(ge=0)
    total_alerts: int = Field(ge=0)
    severity_counts: SeverityCounts


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
