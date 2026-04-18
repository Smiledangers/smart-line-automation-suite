"""Dashboard service layer with async database support."""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.Models.user import User
from app.Models.line_user import LINEUser
from app.Models.scraping_job import ScrapingJob
from app.Models.scraping_result import ScrapingResult
from app.Models.ai_conversation import AIConversation, AIMessage

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management."""

    async def get_user(self, db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID."""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_users(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[User]:
        """Get list of users with pagination."""
        result = await db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create_user(self, db: AsyncSession, user_data: dict) -> User:
        """Create a new user."""
        user = User(**user_data)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update_user(
        self, db: AsyncSession, user_id: int, user_data: dict
    ) -> Optional[User]:
        """Update user."""
        user = await self.get_user(db, user_id)
        if not user:
            return None

        for field, value in user_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(user)
        return user

    async def delete_user(self, db: AsyncSession, user_id: int) -> bool:
        """Delete user."""
        user = await self.get_user(db, user_id)
        if not user:
            return False

        await db.delete(user)
        await db.commit()
        return True

    async def count_users(self, db: AsyncSession) -> int:
        """Count total users."""
        result = await db.execute(select(func.count(User.id)))
        return result.scalar() or 0


class StatsService:
    """Service for dashboard statistics."""

    async def get_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get dashboard statistics."""
        # Count users
        user_result = await db.execute(select(func.count(User.id)))
        user_count = user_result.scalar() or 0

        # Count LINE users
        line_user_result = await db.execute(select(func.count(LINEUser.id)))
        line_user_count = line_user_result.scalar() or 0

        # Count scraping jobs
        job_result = await db.execute(select(func.count(ScrapingJob.id)))
        scraping_job_count = job_result.scalar() or 0

        # Count completed jobs
        completed_result = await db.execute(
            select(func.count(ScrapingJob.id)).where(ScrapingJob.status == "completed")
        )
        completed_job_count = completed_result.scalar() or 0

        # Count failed jobs
        failed_result = await db.execute(
            select(func.count(ScrapingJob.id)).where(ScrapingJob.status == "failed")
        )
        failed_job_count = failed_result.scalar() or 0

        # Count AI conversations
        conv_result = await db.execute(select(func.count(AIConversation.id)))
        ai_conversation_count = conv_result.scalar() or 0

        # Count AI messages
        msg_result = await db.execute(select(func.count(AIMessage.id)))
        ai_message_count = msg_result.scalar() or 0

        return {
            "user_count": user_count,
            "line_user_count": line_user_count,
            "scraping_job_count": scraping_job_count,
            "completed_job_count": completed_job_count,
            "failed_job_count": failed_job_count,
            "ai_conversation_count": ai_conversation_count,
            "ai_message_count": ai_message_count,
            "success_rate": round(
                completed_job_count / scraping_job_count * 100, 2
            )
            if scraping_job_count > 0
            else 0,
        }


class LogsService:
    """Service for operation logs."""

    async def get_logs(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get operation logs (placeholder - implement based on needs)."""
        # This is a placeholder for audit logging
        # You could extend this to have a dedicated AuditLog model
        logger.info(f"Fetching logs for user_id={user_id}, skip={skip}, limit={limit}")
        return []


class DashboardService:
    """Main dashboard service that aggregates sub-services."""

    def __init__(self):
        self.user_service = UserService()
        self.stats_service = StatsService()
        self.logs_service = LogsService()

    async def get_user(
        self, db: AsyncSession, user_id: int
    ) -> Optional[User]:
        return await self.user_service.get_user(db, user_id)

    async def get_users(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[User]:
        return await self.user_service.get_users(db, skip, limit)

    async def create_user(self, db: AsyncSession, user_data: dict) -> User:
        return await self.user_service.create_user(db, user_data)

    async def update_user(
        self, db: AsyncSession, user_id: int, user_data: dict
    ) -> Optional[User]:
        return await self.user_service.update_user(db, user_id, user_data)

    async def delete_user(self, db: AsyncSession, user_id: int) -> bool:
        return await self.user_service.delete_user(db, user_id)

    async def get_stats(self, db: AsyncSession) -> Dict[str, Any]:
        return await self.stats_service.get_stats(db)

    async def get_logs(
        self,
        db: AsyncSession,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        return await self.logs_service.get_logs(db, user_id, skip, limit)


dashboard_service = DashboardService()