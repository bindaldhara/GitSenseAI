from fastapi import APIRouter

from schemas.chat import ChatRequest, ChatResponse
from services.chat_service import chat_with_repository

router = APIRouter(prefix="/repositories/{repository_id}/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def repository_chat(repository_id: int, payload: ChatRequest) -> ChatResponse:
    history = [{"role": item.role, "content": item.content} for item in payload.history]
    result = chat_with_repository(
        repository_id,
        message=payload.message,
        top_k=payload.top_k,
        history=history,
    )
    return ChatResponse.model_validate(result)
