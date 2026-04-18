"""
API Key endpoints for third-party access management.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.api_key import (
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
    APIKeyListResponse,
)
from app.services.api_key_service import api_key_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api-keys", tags=["api-keys"])


async def verify_api_key(
    x_api_key: str = Header(..., description="API Key"),
    db: AsyncSession = Depends(get_db),
):
    """Dependency to verify API key."""
    api_key = await api_key_service.verify_key(db, x_api_key)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")
    return api_key


@router.post("", response_model=APIKeyResponse, status_code=201)
async def create_api_key(
    api_key_data: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    verified_key: Optional[str] = Depends(verify_api_key) if False else None,
):
    """
    Create a new API key.
    Note: In production, require admin authentication.
    """
    api_key = await api_key_service.create(
        db=db,
        name=api_key_data.name,
        user_id=api_key_data.user_id,
        can_send_message=api_key_data.can_send_message,
        can_read_conversation=api_key_data.can_read_conversation,
        can_read_stats=api_key_data.can_read_stats,
        rate_limit_per_minute=api_key_data.rate_limit_per_minute,
        expires_at=api_key_data.expires_at,
        description=api_key_data.description,
    )
    return api_key


@router.get("", response_model=APIKeyListResponse)
async def list_api_keys(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all API keys."""
    keys, total = await api_key_service.get_all(db, user_id=user_id, skip=skip, limit=limit)
    return {"keys": keys, "total": total}


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific API key."""
    api_key = await api_key_service.get_by_id(db, key_id)
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    return api_key


@router.put("/{key_id}", response_model=APIKeyResponse)
async def update_api_key(
    key_id: int,
    api_key_data: APIKeyUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update an API key."""
    api_key = await api_key_service.update(db, key_id, **api_key_data.model_dump(exclude_unset=True))
    if not api_key:
        raise HTTPException(status_code=404, detail="API key not found")
    return api_key


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete an API key."""
    success = await api_key_service.delete(db, key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"status": "success", "message": "API key deleted"}