from fastapi import APIRouter, Response, status

from schemas.repository import (
    RepositoryCreate,
    RepositoryListResponse,
    RepositoryResponse,
)
from services.repository_service import (
    create_repository_submission,
    delete_repository,
    list_repositories,
    reindex_repository,
)

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("", response_model=RepositoryListResponse)
def read_repositories() -> RepositoryListResponse:
    repositories = [RepositoryResponse.model_validate(item) for item in list_repositories()]
    return RepositoryListResponse(repositories=repositories)


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
def submit_repository(payload: RepositoryCreate) -> RepositoryResponse:
    repository = create_repository_submission(str(payload.url))
    return RepositoryResponse.model_validate(repository)


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_repository(repository_id: int) -> Response:
    delete_repository(repository_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{repository_id}/reindex",
    response_model=RepositoryResponse,
    status_code=status.HTTP_200_OK,
)
def reindex_repository_endpoint(repository_id: int) -> RepositoryResponse:
    repository = reindex_repository(repository_id)
    return RepositoryResponse.model_validate(repository)
