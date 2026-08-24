from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.config import settings
from app.api_boundary.boundary import boundary, BoundaryError


@dataclass
class AIAgentActor:
    id: Optional[int]
    actor_kind: str = "ai_agent"


class ChatMessage(BaseModel):
    message: str
    context: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    sources: Optional[list[str]] = None


async def query_ollama(prompt: str, model: str | None = None) -> str:
    model = model or settings.OLLAMA_MODEL
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            f"{settings.OLLAMA_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
        )
        return response.json().get("response", "")


def build_router() -> APIRouter:
    router = APIRouter()

    @router.post("/chat", response_model=ChatResponse)
    async def chat(data: ChatMessage, db: Session = Depends(get_db),
                    current_user=Depends(get_current_user)):
        agent_actor = AIAgentActor(id=current_user.id)

        try:
            finance_summary = boundary.query(
                name="finance.dashboard", actor=agent_actor, db=db,
            )
        except BoundaryError:
            finance_summary = None

        prompt = (
            "You are an AI business assistant for an ERP system. "
            "Answer the user's question concisely and helpfully.\n\n"
            f"Finance summary: {finance_summary}\n\n"
            f"User question: {data.message}"
        )
        response_text = await query_ollama(prompt)
        return ChatResponse(response=response_text, sources=["finance.dashboard"] if finance_summary else [])

    return router
