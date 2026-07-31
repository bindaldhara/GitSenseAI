from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000, description="User question about the repository")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of code chunks to retrieve")
    use_hybrid: bool | None = Field(
        default=None,
        description="Use BM25 + vector hybrid search. Defaults to server HYBRID_SEARCH_ENABLED setting.",
    )
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=20,
        description="Optional prior turns for multi-turn chat (client-managed for now)",
    )


class RetrievedSource(BaseModel):
    file_path: str
    language: str
    chunk_kind: str
    symbol_name: str | None
    start_line: int
    end_line: int
    score: float
    excerpt: str


class ChatResponse(BaseModel):
    repository_id: int
    answer: str
    sources: list[RetrievedSource]
    model: str
    retrieval_mode: Literal["hybrid", "vector"]
