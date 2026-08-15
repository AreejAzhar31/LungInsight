"""
Authentication endpoints: register, login, logout, refresh.

Note on logout: since this backend uses stateless JWTs (no server-side
session table for access/refresh tokens), `/logout` is a client-directed
action — the client discards its stored tokens. The endpoint still exists
so the client has a clear, auditable action to call (and so a future
token-blacklist table can be added here without changing the API contract).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from app.api.dependencies import get_auth_service, get_log_service, CurrentUser
from app.core.exceptions import AppError
from app.middleware.rate_limit import limiter
from app.core.config import get_settings
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    RefreshTokenRequest,
    TokenResponse,
    RegisterResponse,
    MessageResponse,
    UserResponse,
    UserUpdateRequest,
)
from app.services.auth_service import AuthService
from app.services.log_service import LogService

settings = get_settings()
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.rate_limit_auth)
def register(
    request: Request,
    data: UserRegister,
    auth_service: AuthService = Depends(get_auth_service),
    log_service: LogService = Depends(get_log_service),
) -> RegisterResponse:
    try:
        user, tokens = auth_service.register(data)
    except AppError:
        raise
    log_service.record("register", user_id=user.id, ip_address=request.client.host if request.client else None)
    return RegisterResponse(user=user, tokens=tokens)


@router.post("/login", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_auth)
def login(
    request: Request,
    data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
    log_service: LogService = Depends(get_log_service),
) -> TokenResponse:
    user, tokens = auth_service.login(data)
    log_service.record("login", user_id=user.id, ip_address=request.client.host if request.client else None)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit(settings.rate_limit_auth)
def refresh(
    request: Request,
    data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return auth_service.refresh(data.refresh_token)


@router.post("/logout", response_model=MessageResponse)
def logout(
    current_user: CurrentUser,
    request: Request,
    log_service: LogService = Depends(get_log_service),
) -> MessageResponse:
    log_service.record(
        "logout", user_id=current_user.id, ip_address=request.client.host if request.client else None
    )
    return MessageResponse(message="Logged out successfully. Please discard your tokens client-side.")


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUser) -> UserResponse:
    """Backing endpoint for Frontend's getCurrentUser() — previously
    permanently mocked regardless of MOCK_MODE since nothing existed here."""
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    data: UserUpdateRequest,
    current_user: CurrentUser,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserResponse:
    """Backing endpoint for the Settings page's profile save — previously
    that form just showed a fake 'Saved' state without persisting anything."""
    return auth_service.update_profile(current_user, data)
