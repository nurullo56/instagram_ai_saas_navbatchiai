from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse
)
from app.schemas.common import APIResponse
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=APIResponse[TokenResponse], status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    session: AsyncSession = Depends(get_db)
):
    service = AuthService(session)
    user, tenant = await service.register(
        email=data.email,
        password=data.password,
        full_name=data.full_name,
        company_name=data.company_name
    )
    tokens = service.generate_tokens(user.id, tenant.id)
    return APIResponse(
        success=True,
        message="Muvaffaqiyatli ro'yxatdan o'tdingiz",
        data=TokenResponse(**tokens)
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db)
):
    service = AuthService(session)
    user, tenant_id = await service.authenticate(
        email=form_data.username,
        password=form_data.password
    )
    tokens = service.generate_tokens(user.id, tenant_id)
    return TokenResponse(**tokens)


@router.post("/refresh", response_model=APIResponse[TokenResponse])
async def refresh_token(
    data: RefreshTokenRequest,
    session: AsyncSession = Depends(get_db)
):
    service = AuthService(session)
    tokens = await service.refresh_tokens(data.refresh_token)
    return APIResponse(
        success=True,
        message="Tokenlar yangilandi",
        data=TokenResponse(**tokens)
    )


@router.get("/me", response_model=APIResponse[UserResponse])
async def get_me(current_user: User = Depends(get_current_user)):
    return APIResponse(
        success=True,
        data=UserResponse.model_validate(current_user)
    )
