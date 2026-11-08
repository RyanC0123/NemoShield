
import secrets

from fastapi import APIRouter, Header, HTTPException, Query, Response

from app.models.api_schemas import (
    EventListResponse,
    ErrorResponse,
)
from app.config import NEMOSHIELD_INGEST_TOKEN
from app.models.security_event import SecurityEvent, Severity
from app.storage.event_store import (
    DuplicateEventError,
    ingest_security_event,
    load_security_events,
)


router = APIRouter(
    prefix="/api/events",
    tags=["Security Events"]
)



@router.get(
    "",
    response_model=EventListResponse,
    summary="List security events",
    description=(
        "Retrieve seeded and ingested security events with optional severity "
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
    events = load_security_events()

    if severity is not None:
        events = [
            event for event in events
            if event.severity == severity
        ]

    events.sort(key=lambda event: event.timestamp, reverse=True)
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
    events = load_security_events()

    for event in events:
        if event.event_id == event_id:
            return event

    raise HTTPException(
        status_code=404,
        detail="Security event not found"
    )


@router.post(
    "",
    status_code=201,
    summary="Ingest a normalized security event",
    description=(
        "Accept a normalized security event from a trusted collector. "
        "Retries with identical event IDs are idempotent. Configure "
        "NEMOSHIELD_INGEST_TOKEN and send it as a Bearer token."
    ),
    responses={
        200: {"description": "Identical event retry; no duplicate was stored"},
        401: {"model": ErrorResponse, "description": "Invalid ingestion token"},
        409: {"model": ErrorResponse, "description": "Event ID conflict"},
        503: {"model": ErrorResponse, "description": "Ingestion is not configured"},
    },
)
def ingest_event(
    event: SecurityEvent,
    response: Response,
    authorization: str | None = Header(default=None),
):
    expected_token = NEMOSHIELD_INGEST_TOKEN
    if not expected_token:
        raise HTTPException(
            status_code=503,
            detail="Event ingestion is disabled until NEMOSHIELD_INGEST_TOKEN is configured",
        )

    scheme, separator, supplied_token = (authorization or "").partition(" ")
    if (
        not separator
        or scheme.lower() != "bearer"
        or not secrets.compare_digest(supplied_token, expected_token)
    ):
        raise HTTPException(
            status_code=401,
            detail="A valid Bearer ingestion token is required",
        )

    try:
        saved_event, created = ingest_security_event(event)
    except DuplicateEventError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    if not created:
        response.status_code = 200
    return {"event": saved_event, "created": created}
