"""
Auth service — business logic for registration, login, and token refresh.

Services orchestrate repositories + security utilities; they never touch
the DB session directly (that's the repository's job) and never touch
FastAPI request/response objects directly (that's the router's job).
"""

from __future__ import annotations

from app.core.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InactiveUserError,
    InvalidTokenError as AppInvalidTokenError,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    InvalidTokenError as JWTInvalidTokenError,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserUpdateRequest


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def update_profile(self, user: User, data: UserUpdateRequest) -> User:
        if data.full_name is not None:
            user.full_name = data.full_name.strip() or None
        return self.user_repository.update(user)

    def register(self, data: UserRegister) -> tuple[User, TokenResponse]:
        if self.user_repository.email_exists(data.email):
            raise EmailAlreadyRegisteredError()

        user = User(
            email=data.email.lower(),
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
        )
        user = self.user_repository.create(user)
        tokens = self._issue_tokens(user)
        return user, tokens

    def login(self, data: UserLogin) -> tuple[User, TokenResponse]:
        user = self.user_repository.get_by_email(data.email)
        if user is None or not verify_password(data.password, user.hashed_password):
            raise InvalidCredentialsError()
        if not user.is_active:
            raise InactiveUserError()

        tokens = self._issue_tokens(user)
        return user, tokens

    def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            payload = decode_token(refresh_token, expected_type="refresh")
        except JWTInvalidTokenError as exc:
            raise AppInvalidTokenError(str(exc)) from exc

        user_id = payload.get("sub")
        user = self.user_repository.get(user_id) if user_id else None
        if user is None:
            raise AppInvalidTokenError("User for this token no longer exists.")
        if not user.is_active:
            raise InactiveUserError()

        return self._issue_tokens(user)

    def _issue_tokens(self, user: User) -> TokenResponse:
        subject = str(user.id)
        return TokenResponse(
            access_token=create_access_token(subject),
            refresh_token=create_refresh_token(subject),
        )
