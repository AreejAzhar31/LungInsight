"""
Integration tests for AuthService — exercises the service + repository +
DB layers together (no HTTP layer involved), against an isolated SQLite DB.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
import app.models  # noqa: F401
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.schemas.auth import UserRegister, UserLogin
from app.core.exceptions import EmailAlreadyRegisteredError, InvalidCredentialsError


@pytest.fixture()
def session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def auth_service(session):
    return AuthService(UserRepository(session))


def test_register_creates_user_and_issues_tokens(auth_service):
    user, tokens = auth_service.register(UserRegister(email="a@example.com", password="SecurePass123"))
    assert user.email == "a@example.com"
    assert tokens.access_token
    assert tokens.refresh_token


def test_register_duplicate_email_raises(auth_service):
    auth_service.register(UserRegister(email="dupe@example.com", password="SecurePass123"))
    with pytest.raises(EmailAlreadyRegisteredError):
        auth_service.register(UserRegister(email="dupe@example.com", password="AnotherPass456"))


def test_register_email_is_case_insensitive_for_duplicates(auth_service):
    auth_service.register(UserRegister(email="Case@Example.com", password="SecurePass123"))
    with pytest.raises(EmailAlreadyRegisteredError):
        auth_service.register(UserRegister(email="case@example.com", password="AnotherPass456"))


def test_login_success(auth_service):
    auth_service.register(UserRegister(email="login@example.com", password="SecurePass123"))
    user, tokens = auth_service.login(UserLogin(email="login@example.com", password="SecurePass123"))
    assert user.email == "login@example.com"
    assert tokens.access_token


def test_login_wrong_password_raises(auth_service):
    auth_service.register(UserRegister(email="login2@example.com", password="SecurePass123"))
    with pytest.raises(InvalidCredentialsError):
        auth_service.login(UserLogin(email="login2@example.com", password="WrongPassword"))


def test_login_nonexistent_user_raises(auth_service):
    with pytest.raises(InvalidCredentialsError):
        auth_service.login(UserLogin(email="ghost@example.com", password="SecurePass123"))


def test_refresh_issues_new_tokens(auth_service):
    _, tokens = auth_service.register(UserRegister(email="refresh@example.com", password="SecurePass123"))
    new_tokens = auth_service.refresh(tokens.refresh_token)
    assert new_tokens.access_token
    assert new_tokens.refresh_token


def test_refresh_with_access_token_fails(auth_service):
    from app.core.exceptions import InvalidTokenError
    _, tokens = auth_service.register(UserRegister(email="refresh2@example.com", password="SecurePass123"))
    with pytest.raises(InvalidTokenError):
        auth_service.refresh(tokens.access_token)  # wrong token type
