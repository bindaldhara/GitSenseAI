from fastapi import APIRouter, Depends

from auth.dependencies import AuthenticatedUser, get_optional_user, get_user_id_for_scope
from config import settings
from schemas.chat import ChatRequest, ChatResponse
from services.chat_service import chat_with_repository
from services.conversation_service import (
    append_conversation_messages,
    conversation_history_for_chat,
    create_conversation,
    get_conversation,
)

router = APIRouter(prefix="/repositories/{repository_id}/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def repository_chat(
    repository_id: int,
    payload: ChatRequest,
    user: AuthenticatedUser | None = Depends(get_optional_user),
) -> ChatResponse:
    user_id = get_user_id_for_scope(user)
    conversation_id = payload.conversation_id
    history: list[dict[str, str]] = []

    if conversation_id is not None:
        if user is None:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required to use conversation history.",
            )
        conversation = get_conversation(conversation_id, user.id)
        if conversation["repository_id"] != repository_id:
            from fastapi import HTTPException, status

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Conversation does not belong to this repository.",
            )
        history = conversation_history_for_chat(conversation_id, user.id)
    else:
        history = [{"role": item.role, "content": item.content} for item in payload.history]

    result = chat_with_repository(
        repository_id,
        message=payload.message,
        top_k=payload.top_k,
        history=history,
        use_hybrid=payload.use_hybrid,
        use_semantic_cache=payload.use_semantic_cache,
        use_agents=payload.use_agents,
        user_id=user_id,
    )

    if user is not None and settings.auth_enabled:
        if conversation_id is None:
            created = create_conversation(user.id, repository_id, title=payload.message[:80])
            conversation_id = created["id"]
        if conversation_id is not None:
            append_conversation_messages(
                conversation_id,
                user.id,
                user_content=payload.message,
                assistant_content=result["answer"],
                assistant_metadata={
                    "sources": result.get("sources") or [],
                    "model": result.get("model"),
                    "retrieval_mode": result.get("retrieval_mode"),
                    "route": result.get("route"),
                    "agent": result.get("agent"),
                    "cache_hit": result.get("cache_hit"),
                },
            )
            result["conversation_id"] = conversation_id

    return ChatResponse.model_validate(result)
