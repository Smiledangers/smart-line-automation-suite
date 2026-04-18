"""Unit tests for core modules (config, security, database)."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.core.config import Settings, get_settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    get_current_user,
    get_current_active_user,
)
from app.utils.validators import (
    validate_email,
    validate_url,
    validate_line_user_id,
)


class TestConfig:
    """Test configuration module."""

    def test_settings_creation(self):
        """Test Settings can be created with defaults."""
        with patch.dict("os.environ", {"SECRET_KEY": "test-secret-key"}):
            settings = Settings()
            assert settings.SECRET_KEY == "test-secret-key"

    def test_get_settings_singleton(self):
        """Test get_settings returns singleton."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


class TestSecurity:
    """Test security module."""

    def test_password_hashing(self):
        """Test password can be hashed."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed)
    
    def test_verify_wrong_password(self):
        """Test wrong password fails verification."""
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert not verify_password("wrongpassword", hashed)

    def test_create_access_token(self):
        """Test JWT token creation."""
        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(minutes=30)
        )
        
        assert token is not None
        assert isinstance(token, str)

    @pytest.mark.asyncio
    async def test_decode_access_token(self):
        """Test JWT token decoding."""
        token = create_access_token(
            data={"sub": "testuser", "user_id": 1},
            expires_delta=timedelta(minutes=30)
        )
        
        payload = decode_access_token(token)
        
        assert payload is not None
        assert payload.get("sub") == "testuser"
        assert payload.get("user_id") == 1

    def test_decode_invalid_token(self):
        """Test invalid token returns None."""
        payload = decode_access_token("invalid-token")
        assert payload is None


class TestValidators:
    """Test validators module."""

    def test_validate_email_valid(self):
        """Test valid email passes validation."""
        assert validate_email("test@example.com") == "test@example.com"
        assert validate_email("user+tag@domain.co.uk") == "user+tag@domain.co.uk"

    def test_validate_email_invalid(self):
        """Test invalid email raises error."""
        with pytest.raises(ValueError):
            validate_email("not-an-email")
        with pytest.raises(ValueError):
            validate_email("@example.com")
        with pytest.raises(ValueError):
            validate_email("test@")

    def test_validate_url_valid(self):
        """Test valid URL passes validation."""
        assert validate_url("https://example.com") == "https://example.com"
        assert validate_url("http://test.org/path") == "http://test.org/path"

    def test_validate_url_invalid(self):
        """Test invalid URL raises error."""
        with pytest.raises(ValueError):
            validate_url("not-a-url")
        with pytest.raises(ValueError):
            validate_url("ftp://example.com")

    def test_validate_line_user_id_valid(self):
        """Test valid LINE user ID passes validation."""
        assert validate_line_user_id("U1234567890abcdef1234567890abcdef")
        assert validate_line_user_id("U12345678901234567890123456789012")

    def test_validate_line_user_id_invalid(self):
        """Test invalid LINE user ID raises error."""
        with pytest.raises(ValueError):
            validate_line_user_id("invalid")
        with pytest.raises(ValueError):
            validate_line_user_id("C1234567890abcdef1234567890abcdef")


class TestDecorators:
    """Test decorator utilities."""

    def test_retry_decorator_sync(self):
        """Test retry decorator works on sync function."""
        from app.utils.decorators import retry
        
        attempt_count = 0
        
        @retry(max_attempts=3, delay=0.1)
        def failing_function():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise Exception("Fail")
            return "success"
        
        result = failing_function()
        assert result == "success"
        assert attempt_count == 2

    def test_circuit_breaker(self):
        """Test circuit breaker pattern."""
        from app.utils.decorators import CircuitBreaker
        
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # Fail twice to open circuit
        try:
            breaker.call(lambda: (_ for _ in ()).throw(Exception("Fail")))
        except Exception:
            pass
        
        try:
            breaker.call(lambda: (_ for _ in ()).throw(Exception("Fail")))
        except Exception:
            pass
        
        # Circuit should now be open
        assert breaker.state == "open"


class TestLoggingUtils:
    """Test logging utilities."""

    def test_structured_logging(self):
        """Test structured logging works."""
        from app.utils.logging_utils import setup_logging, get_logger
        
        logger = get_logger("test")
        assert logger is not None
        
        # Should be able to log
        logger.info("Test message", extra={"key": "value"})


class TestDatabase:
    """Test database module."""

    @pytest.mark.asyncio
    async def test_get_db_returns_session(self):
        """Test get_db dependency returns async session."""
        from app.core.database import get_db
        
        # This is a generator, need to iterate
        gen = get_db()
        session = await gen.__anext__()
        
        assert session is not None
        # Don't exhaust the generator here