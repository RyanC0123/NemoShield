
from fastapi import APIRouter, Query, HTTPException

from app.models.api_schemas import (
    EventListResponse,
    ErrorResponse,
)
from app.models.security_event import SecurityEvent, Severity
from app.storage.dataset_loader import load_synthetic_events


router = APIRouter(
    prefix="/api/events",
    tags=["Security Events"]
)



@router.get(
    "",
    response_model=EventListResponse,
    summary="List security events",
    description=(
        "Retrieve security events with optional severity "
        "filtering and pagination."
    ),
    responses={
        422: {
            "model": ErrorResponse,
            "description": "Invalid query parameters",
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)
def get_events(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    severity: Severity | None = None,
):
    events = load_synthetic_events()

    if severity is not None:
        events = [
            event for event in events
            if event.severity == severity
        ]

    total = len(events)
    paginated_events = events[offset:offset + limit]

    return EventListResponse(
        events=paginated_events,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{event_id}",
    response_model=SecurityEvent,
    summary="Get a security event by ID",
    description="Retrieve one security event using its unique event ID.",
    responses={
        404: {
            "model": ErrorResponse,
            "description": "Security event not found",
        },
        422: {
            "model": ErrorResponse,
            "description": "Invalid event ID request",
        },
        500: {
            "model": ErrorResponse,
            "description": "Internal server error",
        },
    },
)

def get_event_by_id(event_id: str):
    events = load_synthetic_events()

    for event in events:
        if event.event_id == event_id:
            return event

    raise HTTPException(
        status_code=404,
        detail="Security event not found"
    )
