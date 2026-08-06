"""Repository Mermaid diagram API."""

from fastapi import APIRouter

from diagrams.service import generate_repository_diagram
from schemas.diagram import DiagramRequest, DiagramResponse

router = APIRouter(prefix="/repositories/{repository_id}/diagram", tags=["diagram"])


@router.post("", response_model=DiagramResponse)
def create_repository_diagram(repository_id: int, payload: DiagramRequest) -> DiagramResponse:
    """Generate a Mermaid diagram (import dependencies or architecture)."""
    result = generate_repository_diagram(
        repository_id,
        message=payload.message,
        diagram_type=payload.diagram_type,
        limit=payload.limit,
    )
    return DiagramResponse.model_validate(result)
