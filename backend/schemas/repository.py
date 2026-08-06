from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class RepositoryCreate(BaseModel):
    url: HttpUrl = Field(description="Public GitHub repository URL")


class RepositoryResponse(BaseModel):
    id: int
    url: str
    full_name: str
    provider: str
    status: str
    clone_path: str
    default_branch: str | None
    created_at: datetime
    updated_at: datetime


class RepositoryListResponse(BaseModel):
    repositories: list[RepositoryResponse]


class SymbolResponse(BaseModel):
    id: int
    name: str
    kind: str
    start_line: int
    end_line: int
    signature: str | None
    parent_name: str | None
    file_path: str
    language: str


class SkippedFileResponse(BaseModel):
    path: str
    reason: str


class RepositoryParseSummaryResponse(BaseModel):
    repository_id: int
    file_count: int
    symbol_count: int
    skipped_count: int
    by_language: dict[str, int]
    by_kind: dict[str, int]
    by_skip_reason: dict[str, int]
    skipped_files: list[SkippedFileResponse]
    skipped_returned: int
    skipped_limit: int


class RepositorySymbolsResponse(RepositoryParseSummaryResponse):
    symbols: list[SymbolResponse]
    symbols_returned: int
    symbols_limit: int


class EmbeddingSummaryResponse(BaseModel):
    repository_id: int
    vector_count: int
    bm25_chunk_count: int = 0
    hybrid_ready: bool = False
    graph_node_count: int = 0
    graph_edge_count: int = 0
    graph_ready: bool = False
