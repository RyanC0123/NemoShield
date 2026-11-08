
from fastapi import APIRouter, HTTPException

from app.models.api_schemas import (
    SecurityAlert,
    AlertListResponse,
    ErrorResponse,
)
from app.models.security_event import Severity
from app.storage.alert_store import acknowledge_alert, load_acknowledgments
from app.storage.event_store import load_security_events


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
        "critical severity events. Seeded and ingested events "
        "are not confirmed attacks."
    ),
    responses={
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)

def get_alerts():
    events = load_security_events()
    acknowledgments = load_acknowledgments()
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
                status=(
                    "acknowledged"
                    if f"ALT-{event.event_id}" in acknowledgments
                    else "open"
                ),
            )
            alerts.append(alert)

    return AlertListResponse(
        alerts=alerts,
        total=len(alerts),
    )


@router.post(
    "/{alert_id}/acknowledge",
    summary="Acknowledge a security alert",
    description="Persist an operator acknowledgment for a known alert.",
)
def acknowledge_security_alert(alert_id: str):
    events = load_security_events()
    known_alert_ids = {
        f"ALT-{event.event_id}"
        for event in events
        if event.severity in (Severity.HIGH, Severity.CRITICAL)
    }
    if alert_id not in known_alert_ids:
        raise HTTPException(status_code=404, detail="Security alert not found")

    acknowledgment = acknowledge_alert(alert_id)
    return {
        "alert_id": alert_id,
        "status": "acknowledged",
        "acknowledged_at": acknowledgment["acknowledged_at"],
    }
