from pydantic import BaseModel, Field

from schemas.chat import RetrievedSource


class RetrievalCompareRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)


class RetrievalModeResult(BaseModel):
    mode_id: str
    label: str
    retrieval_mode: str
    retrieval_ms: float
    sources: list[RetrievedSource]


class RetrievalCompareResponse(BaseModel):
    repository_id: int
    question: str
    top_k: int
    results: list[RetrievalModeResult]
