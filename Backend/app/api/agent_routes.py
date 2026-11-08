
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.agent.nemotron_client import NemotronClient


router = APIRouter(
    prefix="/api/agent",
    tags=["AI Agent"]
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    response: str


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
