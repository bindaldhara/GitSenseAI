from pydantic import BaseModel, Field

from schemas.chat import RetrievedSource


class GraphRagCompareRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)


class GraphRagModeResult(BaseModel):
    mode_id: str
    label: str
    description: str
    answer: str
    model: str
    retrieval_mode: str
    sources: list[RetrievedSource]
    graph_context: list[str]
    graph_context_count: int
    elapsed_ms: float


class GraphRagCompareResponse(BaseModel):
    repository_id: int
    question: str
    top_k: int
    graph_node_count: int
    graph_edge_count: int
    results: list[GraphRagModeResult]
