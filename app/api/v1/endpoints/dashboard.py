"""
Dashboard endpoints for admin interface.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.user import User
from app.schemas.dashboard import UserResponse, UserCreate, UserUpdate
from app.services.dashboard_service import dashboard_service
from app.core.security import get_current_active_superuser

router = APIRouter()


@router.get("/users", response_model=List[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Retrieve users. Only accessible by superusers.
    """
    users = dashboard_service.get_users(db, skip=skip, limit=limit)
    return users


@router.post("/users", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Create new user. Only accessible by superusers.
    """
    user = dashboard_service.create_user(db, user_in)
    return user


@router.get("/users/{user_id}", response_model=UserResponse)
def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Get a specific user by id. Only accessible by superusers.
    """
    user = dashboard_service.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=404, detail="User not found"
        )
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Update a user. Only accessible by superusers.
    """
    user = dashboard_service.update_user(db, user_id=user_id, user_in=user_in)
    if not user:
        raise HTTPException(
            status_code=404, detail="User not found"
        )
    return user


@router.delete("/users/{user_id}", response_model=UserResponse)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Delete a user. Only accessible by superusers.
    """
    user = dashboard_service.delete_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=404, detail="User not found"
        )
    return user


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
):
    """
    Get dashboard statistics. Only accessible by superusers.
    """
    stats = dashboard_service.get_stats(db)
    return stats