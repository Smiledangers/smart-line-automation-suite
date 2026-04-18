"""
API Key authentication dependencies.
"""
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.services.api_key_service import api_key_service
from app.Models.api_key import APIKey


async def get_current_api_key(
    x_api_key: str = Header(..., description="API Key"),
    db: AsyncSession = Depends(get_db),
) -> APIKey:
    """Dependency to get current API key with full object."""
    api_key = await api_key_service.verify_key(db, x_api_key)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    return api_key


async def get_api_key_optional(
    x_api_key: Optional[str] = Header(None, description="API Key (optional)"),
    db: AsyncSession = Depends(get_db),
) -> Optional[APIKey]:
    """Dependency to optionally get API key (returns None if not provided)."""
    if not x_api_key:
        return None
    return await api_key_service.verify_key(db, x_api_key)


def require_permission(can_send_message: bool = False, can_read_conversation: bool = False, can_read_stats: bool = False):
    """Factory to create permission checker dependency."""
    async def checker(api_key: APIKey = Depends(get_current_api_key)) -> APIKey:
        if can_send_message and not api_key.can_send_message:
            raise HTTPException(status_code=403, detail="Permission denied: cannot send message")
        if can_read_conversation and not api_key.can_read_conversation:
            raise HTTPException(status_code=403, detail="Permission denied: cannot read conversation")
        if can_read_stats and not api_key.can_read_stats:
            raise HTTPException(status_code=403, detail="Permission denied: cannot read stats")
        return api_key
    return checker