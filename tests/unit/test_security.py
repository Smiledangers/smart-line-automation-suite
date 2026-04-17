"""Unit tests for security module."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
)
from app.core.config import settings


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_get_password_hash(self):
        """Test password hashing."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test correct password verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test incorrect password verification."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = get_password_hash(password)
        assert verify_password(wrong_password, hashed) is False


class TestTokenCreation:
    """Test JWT token creation."""

    def test_create_access_token(self):
        """Test access token creation."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        assert token is not None
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """Test access token with custom expiry."""
        data = {"sub": "test@example.com"}
        expires = timedelta(minutes=30)
        token = create_access_token(data, expires_delta=expires)
        assert token is not None

    def test_create_refresh_token(self):
        """Test refresh token creation."""
        data = {"sub": "test@example.com"}
        token = create_refresh_token(data)
        assert token is not None
        assert len(token) > 0


class TestTokenVerification:
    """Test JWT token verification."""

    def test_decode_access_token(self):
        """Test access token decoding."""
        from jose import jwt
        data = {"sub": "test@example.com"}
        token = create_access_token(data)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "test@example.com"
        assert "exp" in payload

    def test_decode_refresh_token(self):
        """Test refresh token decoding."""
        from jose import jwt
        data = {"sub": "test@example.com"}
        token = create_refresh_token(data)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "test@example.com"
        assert payload["type"] == "refresh"


class TestSecurityConfig:
    """Test security configuration."""

    def test_algorithm(self):
        """Test JWT algorithm."""
        assert settings.ALGORITHM == "HS256"

    def test_token_expiry(self):
        """Test token expiry settings."""
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES > 0
        assert settings.REFRESH_TOKEN_EXPIRE_DAYS > 0