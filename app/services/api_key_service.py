"""
API Key service for managing third-party access keys.
"""
import secrets
import logging
from typing import Optional, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.Models.api_key import APIKey

logger = logging.getLogger(__name__)


class APIKeyService:
    """Service for API Key management."""

    @staticmethod
    async def generate_key() -> str:
        """Generate a secure API key."""
        return f"ska_{secrets.token_urlsafe(32)}"

    @staticmethod
    async def create(
        db: AsyncSession,
        name: str,
        user_id: Optional[int] = None,
        can_send_message: bool = True,
        can_read_conversation: bool = True,
        can_read_stats: bool = False,
        rate_limit_per_minute: int = 60,
        expires_at: Optional[datetime] = None,
        description: Optional[str] = None,
    ) -> APIKey:
        """Create a new API key."""
        key = await APIKeyService.generate_key()
        
        api_key = APIKey(
            key=key,
            name=name,
            user_id=user_id,
            can_send_message=can_send_message,
            can_read_conversation=can_read_conversation,
            can_read_stats=can_read_stats,
            rate_limit_per_minute=rate_limit_per_minute,
            expires_at=expires_at,
            description=description,
        )
        
        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)
        
        logger.info(f"Created API key: {name}")
        return api_key

    @staticmethod
    async def get_by_id(db: AsyncSession, key_id: int) -> Optional[APIKey]:
        """Get API key by ID."""
        result = await db.execute(select(APIKey).where(APIKey.id == key_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_key(db: AsyncSession, key: str) -> Optional[APIKey]:
        """Get API key by key value."""
        result = await db.execute(select(APIKey).where(APIKey.key == key))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[APIKey], int]:
        """Get all API keys."""
        query = select(APIKey)
        count_query = select(APIKey)
        
        if user_id:
            query = query.where(APIKey.user_id == user_id)
            count_query = count_query.where(APIKey.user_id == user_id)
        
        query = query.offset(skip).limit(limit).order_by(APIKey.created_at.desc())
        
        result = await db.execute(query)
        keys = result.scalars().all()
        
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())
        
        return list(keys), total

    @staticmethod
    async def update(
        db: AsyncSession,
        key_id: int,
        **kwargs,
    ) -> Optional[APIKey]:
        """Update an API key."""
        api_key = await APIKeyService.get_by_id(db, key_id)
        if not api_key:
            return None
        
        for key, value in kwargs.items():
            if hasattr(api_key, key) and value is not None:
                setattr(api_key, key, value)
        
        api_key.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(api_key)
        
        logger.info(f"Updated API key: {api_key.name}")
        return api_key

    @staticmethod
    async def delete(db: AsyncSession, key_id: int) -> bool:
        """Delete an API key."""
        api_key = await APIKeyService.get_by_id(db, key_id)
        if not api_key:
            return False
        
        await db.delete(api_key)
        await db.commit()
        
        logger.info(f"Deleted API key: {api_key.name}")
        return True

    @staticmethod
    async def verify_key(db: AsyncSession, key: str) -> Optional[APIKey]:
        """Verify an API key and check permissions."""
        api_key = await APIKeyService.get_by_key(db, key)
        
        if not api_key:
            return None
        
        # Check if active
        if not api_key.is_active:
            logger.warning(f"Inactive API key attempted: {api_key.name}")
            return None
        
        # Check expiration
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            logger.warning(f"Expired API key attempted: {api_key.name}")
            return None
        
        # Update last used
        api_key.last_used_at = datetime.utcnow()
        await db.commit()
        
        return api_key


api_key_service = APIKeyService()