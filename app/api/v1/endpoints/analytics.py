"""
Usage analytics endpoints for monitoring and insights.
"""
import logging
from typing import Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
async def get_overview(
    db: AsyncSession = Depends(get_db),
):
    """Get system overview analytics."""
    from app.Models.user import User
    from app.Models.line_user import LINEUser
    from app.Models.ai_conversation import AIConversation
    from app.Models.scraping_job import ScrapingJob
    from app.Models.api_key import APIKey
    
    # Total users
    user_result = await db.execute(select(func.count(User.id)))
    total_users = user_result.scalar()
    
    # LINE users
    line_result = await db.execute(select(func.count(LINEUser.id)))
    line_users = line_result.scalar()
    
    # Active conversations
    conv_result = await db.execute(
        select(func.count(AIConversation.id)).where(AIConversation.is_active == True)
    )
    active_conversations = conv_result.scalar()
    
    # Scraping jobs
    job_result = await db.execute(select(func.count(ScrapingJob.id)))
    total_jobs = job_result.scalar()
    
    # Active API keys
    key_result = await db.execute(
        select(func.count(APIKey.id)).where(APIKey.is_active == True)
    )
    active_keys = key_result.scalar()
    
    return {
        "total_users": total_users or 0,
        "line_users": line_users or 0,
        "active_conversations": active_conversations or 0,
        "total_scraping_jobs": total_jobs or 0,
        "active_api_keys": active_keys or 0,
    }


@router.get("/messages")
async def get_message_stats(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get message statistics for the last N days."""
    from app.Models.ai_conversation import AIMessage
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Count messages per day
    result = await db.execute(
        select(
            func.date(AIMessage.created_at).label("date"),
            func.count(AIMessage.id).label("count")
        )
        .where(AIMessage.created_at >= start_date)
        .group_by(func.date(AIMessage.created_at))
        .order_by(func.date(AIMessage.created_at))
    )
    
    rows = result.all()
    
    return {
        "period_days": days,
        "total_messages": sum(r.count for r in rows),
        "daily_breakdown": [
            {"date": str(r.date), "count": r.count}
            for r in rows
        ]
    }


@router.get("/platforms")
async def get_platform_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get user count by platform."""
    from app.Models.line_user import LINEUser
    
    result = await db.execute(
        select(LINEUser.platform, func.count(LINEUser.id))
        .group_by(LINEUser.platform)
    )
    
    rows = result.all()
    
    platforms = {}
    for platform, count in rows:
        platforms[platform or "unknown"] = count
    
    return {"platforms": platforms}


@router.get("/api-usage")
async def get_api_usage(
    days: int = Query(30, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get API key usage statistics."""
    from app.Models.api_key import APIKey
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(
            APIKey.name,
            APIKey.can_send_message,
            APIKey.can_read_conversation,
            APIKey.can_read_stats,
            APIKey.last_used_at,
        )
        .where(APIKey.last_used_at >= start_date)
        .order_by(APIKey.last_used_at.desc())
    )
    
    rows = result.all()
    
    return {
        "period_days": days,
        "active_keys": len(rows),
        "usage": [
            {
                "key_name": r.name,
                "last_used": r.last_used_at.isoformat() if r.last_used_at else None,
            }
            for r in rows
        ]
    }


@router.get("/scraping")
async def get_scraping_stats(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    """Get scraping job statistics."""
    from app.Models.scraping_job import ScrapingJob
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    result = await db.execute(
        select(ScrapingJob.status, func.count(ScrapingJob.id))
        .where(ScrapingJob.created_at >= start_date)
        .group_by(ScrapingJob.status)
    )
    
    rows = result.all()
    
    status_counts = {}
    for status, count in rows:
        status_counts[status or "unknown"] = count
    
    return {
        "period_days": days,
        "total_jobs": sum(status_counts.values()),
        "by_status": status_counts,
    }


@router.get("/health")
async def analytics_health():
    """Analytics service health check."""
    return {"status": "healthy", "service": "analytics"}