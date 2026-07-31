from fastapi import APIRouter

from schemas.retrieval_lab import RetrievalCompareRequest, RetrievalCompareResponse
from services.retrieval_lab_service import compare_retrieval_modes

router = APIRouter(prefix="/repositories/{repository_id}/retrieval", tags=["retrieval-lab"])


@router.post("/compare", response_model=RetrievalCompareResponse)
def compare_repository_retrieval(
    repository_id: int,
    payload: RetrievalCompareRequest,
) -> RetrievalCompareResponse:
    """Compare retrieval strategies for the same question (no LLM call)."""
    result = compare_retrieval_modes(
        repository_id,
        message=payload.message,
        top_k=payload.top_k,
    )
    return RetrievalCompareResponse.model_validate(result)
