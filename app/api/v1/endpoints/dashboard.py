"""
Dashboard endpoints for admin interface with async support.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr

from app.core.database import get_db
from app.Models.user import User
from app.services.dashboard_service import dashboard_service
from app.core.security import get_current_active_superuser

logger = logging.getLogger(__name__)
router = APIRouter()


# Request/Response models
class UserResponse(BaseModel):
    """User response model."""
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    """User creation model."""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    password: str


class UserUpdate(BaseModel):
    """User update model."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class StatsResponse(BaseModel):
    """Dashboard statistics response model."""
    user_count: int
    line_user_count: int
    scraping_job_count: int
    completed_job_count: int
    failed_job_count: int
    ai_conversation_count: int
    ai_message_count: int
    success_rate: float


@router.get("/users", response_model=list[UserResponse])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> list[UserResponse]:
    """
    Retrieve users. Only accessible by superusers.
    """
    try:
        users = await dashboard_service.get_users(db, skip=skip, limit=limit)
        return [
            UserResponse(
                id=u.id,
                email=u.email,
                username=u.username,
                full_name=u.full_name,
                is_active=u.is_active,
                is_superuser=u.is_superuser,
                created_at=u.created_at.isoformat() if u.created_at else None,
            )
            for u in users
        ]
    except Exception as e:
        logger.error(f"Error reading users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> UserResponse:
    """
    Create new user. Only accessible by superusers.
    """
    try:
        user_data = user_in.model_dump()
        if user_data.get("password"):
            # Will be hashed in service
            pass
        
        user = await dashboard_service.create_user(db, user_data)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at.isoformat() if user.created_at else None,
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}", response_model=UserResponse)
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> UserResponse:
    """
    Get a specific user by id. Only accessible by superusers.
    """
    try:
        user = await dashboard_service.get_user(db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=404, detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at.isoformat() if user.created_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> UserResponse:
    """
    Update a user. Only accessible by superusers.
    """
    try:
        user_data = {k: v for k, v in user_in.model_dump().items() if v is not None}
        
        user = await dashboard_service.update_user(db, user_id=user_id, user_data=user_data)
        if not user:
            raise HTTPException(
                status_code=404, detail="User not found"
            )
        
        return UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at.isoformat() if user.created_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> None:
    """
    Delete a user. Only accessible by superusers.
    """
    try:
        success = await dashboard_service.delete_user(db, user_id=user_id)
        if not success:
            raise HTTPException(
                status_code=404, detail="User not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> StatsResponse:
    """
    Get dashboard statistics. Only accessible by superusers.
    """
    try:
        stats = await dashboard_service.get_stats(db)
        return StatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/logs")
async def get_logs(
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Get operation logs. Only accessible by superusers.
    """
    try:
        logs = await dashboard_service.get_logs(db, user_id=user_id, skip=skip, limit=limit)
        return {"status": "success", "logs": logs}
    except Exception as e:
        logger.error(f"Error getting logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))