from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from schemas.chat import RetrievedSource


class ConversationCreate(BaseModel):
    repository_id: int
    title: str | None = Field(default=None, max_length=200)


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    repository_id: int
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResponse]


class ConversationMessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: Literal["user", "assistant"]
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ConversationMessagesResponse(BaseModel):
    conversation_id: int
    messages: list[ConversationMessageResponse]
