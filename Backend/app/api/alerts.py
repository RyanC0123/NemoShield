
from fastapi import APIRouter

from app.models.api_schemas import (
    SecurityAlert,
    AlertListResponse,
    ErrorResponse,
)
from app.models.security_event import Severity
from app.storage.dataset_loader import load_synthetic_events


router = APIRouter(
    prefix="/api/alerts",
    tags=["Security Alerts"],
)



@router.get(
    "",
    response_model=AlertListResponse,
    summary="List security alerts",
    description=(
        "Retrieve security alerts generated from high and "
        "critical severity events. Alerts are generated "
        "from the synthetic dataset and are not confirmed attacks."
    ),
    responses={
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)

def get_alerts():
    events = load_synthetic_events()
    alerts = []

    for event in events:
        if event.severity in (Severity.HIGH, Severity.CRITICAL):
            alert = SecurityAlert(
                alert_id=f"ALT-{event.event_id}",
                event_id=event.event_id,
                severity=event.severity.value,
                message=(
                    f"{event.severity.value.upper()} severity "
                    f"{event.event_type.value} event "
                    "requires investigation."
                ),
                status="open",
            )
            alerts.append(alert)

    return AlertListResponse(
        alerts=alerts,
        total=len(alerts),
    )
