"""
API v1 router configuration.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.core.config import get_settings
from app.api.v1.endpoints import line, dashboard, scraping, ai, auth, system

settings = get_settings()

# Create main API router for v1 with API_V1_STR prefix
api_router = APIRouter(prefix=settings.API_V1_STR)

# Include sub-routers
api_router.include_router(auth.router, prefix="", tags=["auth"])
api_router.include_router(line.router, prefix="/line", tags=["line"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(scraping.router, prefix="/scraping", tags=["scraping"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(system.router, prefix="", tags=["system"])