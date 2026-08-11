"""Repository Mermaid diagram API."""

from fastapi import APIRouter

from diagrams.service import generate_repository_diagram
from schemas.diagram import DiagramRequest, DiagramResponse

router = APIRouter(prefix="/repositories/{repository_id}/diagram", tags=["diagram"])


@router.post("", response_model=DiagramResponse)
def create_repository_diagram(repository_id: int, payload: DiagramRequest) -> DiagramResponse:
    """Generate a Mermaid import flowchart from the knowledge graph (LLM fallback if needed)."""
    result = generate_repository_diagram(
        repository_id,
        message=payload.message,
        limit=payload.limit,
    )
    return DiagramResponse.model_validate(result)
