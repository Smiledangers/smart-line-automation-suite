"""
Application configuration module.
"""
from pydantic import AnyHttpUrl, BaseSettings, PostgresDsn, validator
from pydantic.networks import EmailStr
from typing import List, Optional, Union


class Settings(BaseSettings):
    PROJECT_NAME: str = "Smart LINE Bot + Dashboard + Scraper Pipeline"
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    # Server
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000

    # Security
    SECRET_KEY: str = "changethis-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "demo_project"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: Optional[PostgresDsn] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> Any:
        if isinstance(v, str):
            return v
        return PostgresDsn.build(
            scheme="postgresql",
            user=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=str(values.get("POSTGRES_PORT")),
            path=f"/{values.get('POSTGRES_DB') or ''}",
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[AnyHttpUrl] = None

    @validator("REDIS_URL", pre=True)
    def assemble_redis_connection(cls, v: Optional[str], values: dict) -> Any:
        if isinstance(v, str):
            return v
        return AnyHttpUrl.build(
            scheme="redis",
            host=values.get("REDIS_HOST"),
            port=str(values.get("REDIS_PORT")),
            password=values.get("REDIS_PASSWORD"),
        )

    # LINE Bot
    LINE_CHANNEL_ACCESS_TOKEN: str = ""
    LINE_CHANNEL_SECRET: str = ""
    LINE_REDIRECT_URI: str = "http://localhost:8000/api/v1/line/callback"

    # AI / LLM
    OPENAI_API_KEY: Optional[str] = None
    # For local models
    LOCAL_LLM_MODEL_PATH: Optional[str] = None
    LOCAL_LLM_TYPE: Optional[str] = None

    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[EmailStr] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_TO_EMAIL: Optional[List[EmailStr]] = []

    # Superuser
    FIRST_SUPERUSER: EmailStr
    FIRST_SUPERUSER_PASSWORD: str

    # Monitoring
    SENTRY_DSN: Optional[AnyHttpUrl] = None
    PROMETHEUS_PORT: int = 9090

    # Scraping
    USER_AGENT: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )
    REQUEST_DELAY: float = 1.0
    MAX_RETRIES: int = 3

    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    @validator("CELERY_BROKER_URL", "CELERY_RESULT_BACKEND", pre=True)
    def assemble_celery_url(cls, v: Optional[str], values: dict) -> Any:
        if isinstance(v, str):
            return v
        return f"redis://{values.get('REDIS_HOST')}:{values.get('REDIS_PORT')}/0"

    # Environment
    ENVIRONMENT: str = "local"
    DEBUG: bool = False

    # Testing
    TESTING: bool = False

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()