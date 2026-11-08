from fastapi import APIRouter, HTTPException, Query

from app.storage.trace_store import load_traces


router = APIRouter(
    prefix="/api/traces",
    tags=["Investigation Traces"],
)


@router.get("")
def get_traces(
    event_id: str | None = None,
    operation: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
):
    traces = load_traces(event_id=event_id, operation=operation)
    return {
        "traces": traces[:limit],
        "total": len(traces),
        "limit": limit,
    }
