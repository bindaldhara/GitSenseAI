from pydantic import BaseModel, Field

from schemas.chat import RetrievedSource


class MultiRepoSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    repository_ids: list[int] | None = Field(
        default=None,
        description="Optional subset of repository ids to search. Defaults to all accessible repos.",
    )
    top_k: int = Field(default=5, ge=1, le=20)
    use_hybrid: bool | None = None


class RepositorySearchResult(BaseModel):
    repository_id: int
    full_name: str
    retrieval_mode: str
    hits: list[RetrievedSource]


class MultiRepoSearchResponse(BaseModel):
    query: str
    repository_count: int
    results: list[RepositorySearchResult]
