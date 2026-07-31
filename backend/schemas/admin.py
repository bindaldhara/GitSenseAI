from pydantic import BaseModel


class ServiceHealth(BaseModel):
    name: str
    status: str
    detail: str | None = None


class RepositoryOpsRow(BaseModel):
    repository_id: int
    full_name: str
    status: str
    chat_ready: bool
    hybrid_ready: bool


class PlatformConfig(BaseModel):
    app_version: str
    llm_provider: str
    ollama_model: str
    openai_model: str
    embedding_model: str
    embedding_dimension: int
    rerank_model: str
    hybrid_search_enabled: bool
    rerank_enabled: bool


class PlatformTotals(BaseModel):
    repository_count: int
    cloned_repository_count: int
    chat_ready_repository_count: int
    hybrid_ready_repository_count: int


class OpsDashboardResponse(BaseModel):
    services: list[ServiceHealth]
    totals: PlatformTotals
    config: PlatformConfig
    repositories: list[RepositoryOpsRow]
