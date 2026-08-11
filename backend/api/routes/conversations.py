from fastapi import APIRouter, Depends, Query

from auth.dependencies import AuthenticatedUser, require_user
from schemas.conversation import (
    ConversationCreate,
    ConversationListResponse,
    ConversationMessagesResponse,
    ConversationMessageResponse,
    ConversationResponse,
)
from services.conversation_service import (
    create_conversation,
    get_conversation,
    list_conversation_messages,
    list_conversations,
)
from services.repository_service import get_repository_by_id

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=ConversationListResponse)
def read_conversations(
    user: AuthenticatedUser = Depends(require_user),
    repository_id: int | None = Query(default=None),
) -> ConversationListResponse:
    rows = list_conversations(user.id, repository_id=repository_id)
    return ConversationListResponse(
        conversations=[ConversationResponse.model_validate(row) for row in rows],
    )


@router.post("", response_model=ConversationResponse, status_code=201)
def create_new_conversation(
    payload: ConversationCreate,
    user: AuthenticatedUser = Depends(require_user),
) -> ConversationResponse:
    get_repository_by_id(payload.repository_id, user_id=user.id)
    row = create_conversation(user.id, payload.repository_id, title=payload.title)
    return ConversationResponse.model_validate(row)


@router.get("/{conversation_id}", response_model=ConversationResponse)
def read_conversation(
    conversation_id: int,
    user: AuthenticatedUser = Depends(require_user),
) -> ConversationResponse:
    row = get_conversation(conversation_id, user.id)
    return ConversationResponse.model_validate(row)


@router.get("/{conversation_id}/messages", response_model=ConversationMessagesResponse)
def read_conversation_messages(
    conversation_id: int,
    user: AuthenticatedUser = Depends(require_user),
) -> ConversationMessagesResponse:
    rows = list_conversation_messages(conversation_id, user.id)
    return ConversationMessagesResponse(
        conversation_id=conversation_id,
        messages=[ConversationMessageResponse.model_validate(row) for row in rows],
    )
