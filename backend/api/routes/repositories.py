from fastapi import APIRouter, status

from schemas.repository import (
    RepositoryCreate,
    RepositoryListResponse,
    RepositoryResponse,
)
from services.repository_service import create_repository_submission, list_repositories

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("", response_model=RepositoryListResponse)
def read_repositories() -> RepositoryListResponse:
    repositories = [RepositoryResponse.model_validate(item) for item in list_repositories()]
    return RepositoryListResponse(repositories=repositories)


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
def submit_repository(payload: RepositoryCreate) -> RepositoryResponse:
    repository = create_repository_submission(str(payload.url))
    return RepositoryResponse.model_validate(repository)
