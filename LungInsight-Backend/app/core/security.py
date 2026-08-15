"""
Security utilities: password hashing (bcrypt) and JWT access/refresh tokens.
"""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
import uuid

from jose import jwt, JWTError
import bcrypt

from app.core.config import get_settings

settings = get_settings()

_BCRYPT_MAX_BYTES = 72  # bcrypt's hard limit; longer inputs are truncated, per bcrypt's own design


# ---- password hashing --------------------------------------------------

def hash_password(plain_password: str) -> str:
    password_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except ValueError:
        return False


# ---- JWT tokens ----------------------------------------------------------

TokenType = Literal["access", "refresh"]


def _create_token(subject: str, expires_delta: timedelta, token_type: TokenType) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),  # unique token id, enables future revocation/blacklisting
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(subject: str) -> str:
    return _create_token(
        subject,
        timedelta(minutes=settings.access_token_expire_minutes),
        "access",
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject,
        timedelta(days=settings.refresh_token_expire_days),
        "refresh",
    )


class InvalidTokenError(Exception):
    pass


def decode_token(token: str, expected_type: TokenType | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise InvalidTokenError(str(exc)) from exc

    if expected_type is not None and payload.get("type") != expected_type:
        raise InvalidTokenError(f"Expected a {expected_type} token, got {payload.get('type')}")

    return payload
