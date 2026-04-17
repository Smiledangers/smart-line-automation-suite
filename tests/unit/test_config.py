"""Unit tests for config module."""
import pytest
from app.core.config import Settings, get_settings


class TestSettings:
    """Test Settings class."""

    def test_default_values(self):
        """Test default configuration values."""
        settings = Settings()
        assert settings.PROJECT_NAME == "Smart LINE Bot + Dashboard + Scraper Pipeline"
        assert settings.VERSION == "1.0.0"
        assert settings.ENVIRONMENT == "development"
        assert settings.DEBUG is True

    def test_database_url_default(self):
        """Test default database URL."""
        settings = Settings()
        assert "postgresql" in settings.DATABASE_URL
        assert "demo_project" in settings.DATABASE_URL

    def test_redis_url_default(self):
        """Test default Redis URL."""
        settings = Settings()
        assert "redis" in settings.REDIS_URL
        assert settings.REDIS_PORT == 6379

    def test_circuit_breaker_defaults(self):
        """Test circuit breaker default values."""
        settings = Settings()
        assert settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD == 5
        assert settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT == 60

    def test_cors_origins_default(self):
        """Test CORS origins default."""
        settings = Settings()
        assert "http://localhost:3000" in settings.BACKEND_CORS_ORIGINS
        assert "http://localhost:8000" in settings.BACKEND_CORS_ORIGINS


class TestGetSettings:
    """Test get_settings function."""

    def test_cached_settings(self):
        """Test that settings are cached."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2