"""
api/v1/endpoints/chat.py
------------------------
Conversational AI Copilot Assistant endpoint.
"""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter
from pydantic import BaseModel, Field
from services.ai_service import ai_service

router = APIRouter(tags=["Joule Assistant Chat"])


class ChatMessageModel(BaseModel):
    role: str = Field(..., description="'user' or 'assistant'")
    content: str = Field(..., description="Message text")


class ChatRequest(BaseModel):
    messages: List[ChatMessageModel] = Field(..., description="Conversation history")


@router.post("/chat")
async def chat(req: ChatRequest) -> Dict[str, str]:
    """Processes conversational questions regarding ST22, CDS, and CTS."""
    raw_msgs = [{"role": m.role, "content": m.content} for m in req.messages]
    reply = await ai_service.chat(raw_msgs)
    return {"reply": reply}
