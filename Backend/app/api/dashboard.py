
from fastapi import APIRouter

from app.models.api_schemas import (
    DashboardSummaryResponse,
    SeverityCounts,
    ErrorResponse,
)
from app.models.security_event import Severity
from app.storage.dataset_loader import load_synthetic_events


router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
)



@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get dashboard security summary",
    description=(
        "Retrieve total security events, total alerts, "
        "and event counts grouped by severity. "
        "Alerts are generated from high and critical "
        "severity events in the synthetic dataset."
    ),
    responses={
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)

def get_dashboard_summary():
    events = load_synthetic_events()

    severity_counts = {
        "low": 0,
        "medium": 0,
        "high": 0,
        "critical": 0,
    }

    for event in events:
        severity_counts[event.severity.value] += 1

    total_alerts = (
        severity_counts["high"]
        + severity_counts["critical"]
    )

    return DashboardSummaryResponse(
        total_events=len(events),
        total_alerts=total_alerts,
        severity_counts=SeverityCounts(**severity_counts),
    )
