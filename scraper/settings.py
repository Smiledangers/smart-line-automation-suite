"""Scraper settings and configuration."""
import os
from typing import Optional

# Botasaurus Settings
BOTASAURUS_VERSION = "1.0.0"

# Request Settings
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_DELAY = 5
DEFAULT_RATE_LIMIT = 1.0  # seconds between requests

# User Agent
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Proxy Settings (optional)
PROXY_ENABLED = os.getenv("SCRAPER_PROXY_ENABLED", "false").lower() == "true"
PROXY_URL = os.getenv("SCRAPER_PROXY_URL", "")

# Database Settings
SCRAPER_DB_ENABLED = os.getenv("SCRAPER_DB_ENABLED", "true").lower() == "true"
SCRAPER_DB_URL = os.getenv("SCRAPER_DB_URL", "")

# Logging Settings
LOG_LEVEL = os.getenv("SCRAPER_LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("SCRAPER_LOG_FILE", "scraper.log")

# Spider Settings
SPIDER_CONCURRENT_REQUESTS = 8
SPIDER_DOWNLOAD_DELAY = 1.0
SPIDER_AUTOTHROTTLE_ENABLED = True
SPIDER_AUTOTHROTTLE_START_DELAY = 1.0
SPIDER_AUTOTHROTTLE_MAX_DELAY = 10.0

# Middleware Settings
RETRY_MIDDLEWARE_ENABLED = True
RATE_LIMIT_MIDDLEWARE_ENABLED = True
ERROR_LOGGING_MIDDLEWARE_ENABLED = True

# Pipeline Settings
CLEANING_PIPELINE_ENABLED = True
STORAGE_PIPELINE_ENABLED = True
STORAGE_TYPE = os.getenv("SCRAPER_STORAGE_TYPE", "file")  # "file" or "db"

# Output Settings
OUTPUT_FORMAT = "jsonl"  # "json", "jsonl", "csv"
OUTPUT_DIR = os.getenv("SCRAPER_OUTPUT_DIR", "output")


class ScraperSettings:
    """Scraper settings class."""

    def __init__(self):
        self.timeout = DEFAULT_TIMEOUT
        self.max_retries = DEFAULT_MAX_RETRIES
        self.retry_delay = DEFAULT_RETRY_DELAY
        self.rate_limit = DEFAULT_RATE_LIMIT
        self.user_agent = DEFAULT_USER_AGENT
        self.proxy_enabled = PROXY_ENABLED
        self.proxy_url = PROXY_URL

    @classmethod
    def from_env(cls) -> "ScraperSettings":
        """Load settings from environment variables."""
        settings = cls()
        settings.timeout = int(os.getenv("SCRAPER_TIMEOUT", DEFAULT_TIMEOUT))
        settings.max_retries = int(os.getenv("SCRAPER_MAX_RETRIES", DEFAULT_MAX_RETRIES))
        settings.retry_delay = int(os.getenv("SCRAPER_RETRY_DELAY", DEFAULT_RETRY_DELAY))
        settings.rate_limit = float(os.getenv("SCRAPER_RATE_LIMIT", DEFAULT_RATE_LIMIT))
        settings.user_agent = os.getenv("SCRAPER_USER_AGENT", DEFAULT_USER_AGENT)
        settings.proxy_enabled = os.getenv("SCRAPER_PROXY_ENABLED", "false").lower() == "true"
        settings.proxy_url = os.getenv("SCRAPER_PROXY_URL", "")
        return settings

    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        return {
            "timeout": self.timeout,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "rate_limit": self.rate_limit,
            "user_agent": self.user_agent,
            "proxy_enabled": self.proxy_enabled,
            "proxy_url": self.proxy_url,
        }


# Default settings instance
default_settings = ScraperSettings()