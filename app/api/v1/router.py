"""
API v1 router.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import line, dashboard, scraping, ai

api_router = APIRouter()
api_router.include_router(line.router, prefix="/line", tags=["line"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(scraping.router, prefix="/scraping", tags=["scraping"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])