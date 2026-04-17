"""System health and status endpoints."""
from fastapi import APIRouter
from datetime import datetime
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime


class ReadyResponse(BaseModel):
    status: str
    database: str
    redis: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Basic health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        timestamp=datetime.utcnow()
    )


@router.get("/ready", response_model=ReadyResponse)
async def readiness_check():
    """Readiness check - verify dependencies are available."""
    db_status = "unknown"
    redis_status = "unknown"

    # Check database
    try:
        from app.core.database import engine
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        db_status = "ready"
    except Exception:
        db_status = "not ready"

    # Check redis
    try:
        import redis
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        redis_status = "ready"
    except Exception:
        redis_status = "not ready"

    all_ready = db_status == "ready" and redis_status == "ready"

    return ReadyResponse(
        status="ready" if all_ready else "not ready",
        database=db_status,
        redis=redis_status
    )


@router.get("/info")
async def system_info():
    """Get system information."""
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "api_v1_str": settings.API_V1_STR,
    }