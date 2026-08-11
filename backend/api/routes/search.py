from fastapi import APIRouter, Depends

from auth.dependencies import AuthenticatedUser, get_optional_user
from config import settings
from schemas.search import MultiRepoSearchRequest, MultiRepoSearchResponse, RepositorySearchResult
from services.multi_repo_search_service import search_across_repositories

router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=MultiRepoSearchResponse)
def search_repositories(
    payload: MultiRepoSearchRequest,
    user: AuthenticatedUser | None = Depends(get_optional_user),
) -> MultiRepoSearchResponse:
    if settings.auth_enabled and user is None:
        user_id = None
        public_only = True
    elif settings.auth_enabled and user is not None:
        user_id = user.id
        public_only = False
    else:
        user_id = None
        public_only = False

    from services.repository_service import list_repositories

    accessible_ids = None
    if public_only:
        accessible_ids = [repo["id"] for repo in list_repositories(public_only=True)]
    elif user_id is not None:
        accessible_ids = [repo["id"] for repo in list_repositories(user_id=user_id)]

    repository_ids = payload.repository_ids
    if accessible_ids is not None:
        if repository_ids:
            repository_ids = [rid for rid in repository_ids if rid in accessible_ids]
        else:
            repository_ids = accessible_ids

    result = search_across_repositories(
        payload.query,
        user_id=user_id if not public_only else None,
        repository_ids=repository_ids,
        top_k=payload.top_k,
        use_hybrid=payload.use_hybrid,
    )
    return MultiRepoSearchResponse(
        query=result["query"],
        repository_count=result["repository_count"],
        results=[RepositorySearchResult.model_validate(item) for item in result["results"]],
    )
