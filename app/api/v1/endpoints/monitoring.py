"""System health check and metrics endpoint."""
from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.core.database import get_db

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> Dict[str, Any]:
    """
    Comprehensive health check including database and Redis.
    """
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {},
    }

    # Check database
    try:
        await db.execute(text("SELECT 1"))
        health["services"]["database"] = {
            "status": "healthy",
            "type": "postgresql",
        }
    except Exception as e:
        health["services"]["database"] = {
            "status": "unhealthy",
            "type": "postgresql",
            "error": str(e),
        }
        health["status"] = "unhealthy"

    # Check Redis
    try:
        import redis.asyncio as aioredis
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await redis_client.ping()
        await redis_client.close()
        health["services"]["redis"] = {
            "status": "healthy",
            "type": "redis",
        }
    except Exception as e:
        health["services"]["redis"] = {
            "status": "unhealthy",
            "type": "redis",
            "error": str(e),
        }
        health["status"] = "degraded"

    # Check LINE API (if configured)
    if settings.LINE_CHANNEL_ACCESS_TOKEN:
        health["services"]["line_api"] = {
            "status": "configured",
            "type": "line",
        }

    # Check OpenAI (if configured)
    if settings.OPENAI_API_KEY:
        health["services"]["openai"] = {
            "status": "configured",
            "type": "openai",
        }

    return health


@router.get("/metrics")
async def metrics() -> Dict[str, Any]:
    """
    Return application metrics summary.
    """
    return {
        "app_name": "smart-line-automation-suite",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "features": {
            "line_bot": bool(settings.LINE_CHANNEL_ACCESS_TOKEN),
            "ai_chat": bool(settings.OPENAI_API_KEY),
            "scraping": True,
            "dashboard": True,
        },
    }


@router.get("/readiness")
async def readiness_check(db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    """
    Readiness check for Kubernetes liveness probe.
    """
    # Check database connection
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        return {"status": "not ready", "reason": "database unavailable"}

    return {"status": "ready"}


@router.get("/startup")
async def startup_check() -> Dict[str, str]:
    """
    Startup check for Kubernetes startup probe.
    """
    return {"status": "started"}