
import logging
import os
from time import perf_counter

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import NVIDIA_API_KEY
from app.agent.nemotron_client import NemotronClient
from app.storage.trace_store import record_trace

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/agent",
    tags=["AI Agent"]
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    response: str


@router.get("/status")
def agent_status():
    mock_mode = os.getenv("NEMOSHIELD_AI_MOCK_MODE", "false").lower() == "true"
    return {
        "configured": bool(NVIDIA_API_KEY),
        "mode": "mock" if mock_mode else "nemotron",
        "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "test_available": bool(NVIDIA_API_KEY) and not mock_mode,
    }


@router.post("/test")
def test_nemotron_connection():
    if not NVIDIA_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="NVIDIA_API_KEY is not configured",
        )
    if os.getenv("NEMOSHIELD_AI_MOCK_MODE", "false").lower() == "true":
        raise HTTPException(
            status_code=409,
            detail="Disable mock mode to test the live Nemotron connection",
        )

    started_at = perf_counter()
    try:
        answer = NemotronClient().generate_response(
            "Reply with exactly NEMOSHIELD_OK."
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=503,
            detail="Nemotron connection is not configured correctly",
        ) from exc
    except Exception as exc:
        logger.exception("Nemotron connectivity test failed")
        raise HTTPException(
            status_code=502,
            detail="Nemotron connection test failed",
        ) from exc

    if not answer.strip():
        raise HTTPException(
            status_code=502,
            detail="Nemotron returned an empty response",
        )

    return {
        "ok": True,
        "model": "nvidia/nemotron-3.5-lightning-30b-a3b",
        "latency_ms": round((perf_counter() - started_at) * 1000),
    }


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty"
        )

    try:
        client = NemotronClient()
        answer = client.generate_response(request.message)
        record_trace(
            operation="agent_chat",
            status="completed",
            steps=[{"name": "nemotron_chat", "status": "completed"}],
            result={"response_characters": len(answer)},
        )

        return ChatResponse(response=answer)

    except ValueError:
        raise HTTPException(
            status_code=503,
            detail="AI service configuration unavailable"
        )

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="AI model request failed"
        )
