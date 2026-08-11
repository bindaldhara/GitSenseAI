from fastapi import APIRouter, Depends

from auth.dependencies import AuthenticatedUser, require_user
from auth.security import create_access_token
from schemas.auth import AuthTokenResponse, LoginRequest, RegisterRequest, UserResponse
from services.user_service import authenticate_user, get_user_by_id, register_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthTokenResponse, status_code=201)
def register(payload: RegisterRequest) -> AuthTokenResponse:
    user = register_user(payload.email, payload.password)
    token = create_access_token(user["id"], user["email"])
    return AuthTokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: LoginRequest) -> AuthTokenResponse:
    user = authenticate_user(payload.email, payload.password)
    token = create_access_token(user["id"], user["email"])
    return AuthTokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def read_current_user(user: AuthenticatedUser = Depends(require_user)) -> UserResponse:
    row = get_user_by_id(user.id)
    if row is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserResponse.model_validate(row)
