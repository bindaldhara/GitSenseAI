from fastapi import APIRouter, Depends

from auth.dependencies import AuthenticatedUser, require_user
from schemas.auth import UserResponse
from services.user_service import get_user_by_id

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=UserResponse)
def read_current_user(user: AuthenticatedUser = Depends(require_user)) -> UserResponse:
    row = get_user_by_id(user.id)
    if row is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserResponse.model_validate(row)
