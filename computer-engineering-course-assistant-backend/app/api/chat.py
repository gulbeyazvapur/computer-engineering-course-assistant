from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import ChatRequest, ChatResponse
from app.services import rag_service


router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    result = rag_service.answer_question(
        payload.question,
        payload.courseId,
    )
    return ChatResponse(**result)
