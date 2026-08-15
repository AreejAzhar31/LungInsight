"""Unit tests for app.core.security (password hashing + JWT tokens)."""
import time
import pytest

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    InvalidTokenError,
)


def test_hash_password_produces_different_hash_each_time():
    h1 = hash_password("SamePassword123")
    h2 = hash_password("SamePassword123")
    assert h1 != h2  # bcrypt salts randomly


def test_verify_password_correct():
    hashed = hash_password("CorrectHorseBattery")
    assert verify_password("CorrectHorseBattery", hashed) is True


def test_verify_password_incorrect():
    hashed = hash_password("CorrectHorseBattery")
    assert verify_password("WrongPassword", hashed) is False


def test_verify_password_handles_garbage_hash_gracefully():
    assert verify_password("anything", "not-a-real-bcrypt-hash") is False


def test_long_password_is_handled_without_error():
    long_password = "a" * 200
    hashed = hash_password(long_password)
    assert verify_password(long_password, hashed) is True


def test_create_and_decode_access_token():
    token = create_access_token(subject="user-123")
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"


def test_create_and_decode_refresh_token():
    token = create_refresh_token(subject="user-456")
    payload = decode_token(token, expected_type="refresh")
    assert payload["sub"] == "user-456"
    assert payload["type"] == "refresh"


def test_decode_token_wrong_expected_type_raises():
    access_token = create_access_token(subject="user-789")
    with pytest.raises(InvalidTokenError):
        decode_token(access_token, expected_type="refresh")


def test_decode_garbage_token_raises():
    with pytest.raises(InvalidTokenError):
        decode_token("not.a.valid.jwt", expected_type="access")


def test_each_token_has_unique_jti():
    token1 = create_access_token(subject="user-1")
    token2 = create_access_token(subject="user-1")
    payload1 = decode_token(token1, expected_type="access")
    payload2 = decode_token(token2, expected_type="access")
    assert payload1["jti"] != payload2["jti"]
