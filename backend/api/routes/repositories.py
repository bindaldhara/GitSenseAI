from fastapi import APIRouter, Query, Response, status

from parsers import get_repository_parse_summary, get_repository_symbols
from schemas.repository import (
    EmbeddingSummaryResponse,
    RepositoryCreate,
    RepositoryListResponse,
    RepositoryParseSummaryResponse,
    RepositoryResponse,
    RepositorySymbolsResponse,
)
from services.repository_service import (
    create_repository_submission,
    delete_repository,
    list_repositories,
    reindex_repository,
)
from vector_store import get_embedding_summary

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("", response_model=RepositoryListResponse)
def read_repositories() -> RepositoryListResponse:
    repositories = [RepositoryResponse.model_validate(item) for item in list_repositories()]
    return RepositoryListResponse(repositories=repositories)


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
def submit_repository(payload: RepositoryCreate) -> RepositoryResponse:
    repository = create_repository_submission(str(payload.url))
    return RepositoryResponse.model_validate(repository)


@router.get(
    "/{repository_id}/parse-summary",
    response_model=RepositoryParseSummaryResponse,
)
def read_repository_parse_summary(
    repository_id: int,
    skipped_limit: int = Query(default=100, ge=1, le=1000),
) -> RepositoryParseSummaryResponse:
    payload = get_repository_parse_summary(
        repository_id,
        skipped_limit=skipped_limit,
    )
    return RepositoryParseSummaryResponse.model_validate(payload)


@router.get("/{repository_id}/symbols", response_model=RepositorySymbolsResponse)
def read_repository_symbols(
    repository_id: int,
    limit: int = Query(default=1000, ge=1, le=10000),
    skipped_limit: int = Query(default=100, ge=1, le=1000),
) -> RepositorySymbolsResponse:
    payload = get_repository_symbols(
        repository_id,
        limit=limit,
        skipped_limit=skipped_limit,
    )
    return RepositorySymbolsResponse.model_validate(payload)


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_repository(repository_id: int) -> Response:
    delete_repository(repository_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/{repository_id}/embedding-summary",
    response_model=EmbeddingSummaryResponse,
)
def read_repository_embedding_summary(repository_id: int) -> EmbeddingSummaryResponse:
    payload = get_embedding_summary(repository_id)
    return EmbeddingSummaryResponse.model_validate(payload)


@router.post(
    "/{repository_id}/reindex",
    response_model=RepositoryResponse,
    status_code=status.HTTP_200_OK,
)
def reindex_repository_endpoint(repository_id: int) -> RepositoryResponse:
    repository = reindex_repository(repository_id)
    return RepositoryResponse.model_validate(repository)
