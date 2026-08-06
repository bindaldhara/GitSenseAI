"""Repository graph (Graph RAG) API routes."""

from fastapi import APIRouter, Query

from graph_rag.service import get_repository_graph_dependencies, get_repository_graph_summary
from schemas.graph import GraphDependenciesResponse, GraphSummaryResponse

router = APIRouter(prefix="/repositories/{repository_id}/graph", tags=["graph"])


@router.get("/summary", response_model=GraphSummaryResponse)
def read_repository_graph_summary(repository_id: int) -> GraphSummaryResponse:
    """Return knowledge graph node/edge counts for a repository."""
    return GraphSummaryResponse.model_validate(get_repository_graph_summary(repository_id))


@router.get("/dependencies", response_model=GraphDependenciesResponse)
def read_repository_graph_dependencies(
    repository_id: int,
    limit: int = Query(default=100, ge=1, le=500),
) -> GraphDependenciesResponse:
    """Return file → module import edges for dependency mapping."""
    payload = get_repository_graph_dependencies(repository_id, limit=limit)
    return GraphDependenciesResponse.model_validate(payload)
