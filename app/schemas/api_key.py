"""
API Key schemas for Pydantic models.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    """Schema for creating API key."""
    name: str = Field(..., description="Name for this API key")
    user_id: Optional[int] = Field(None, description="Owner user ID")
    can_send_message: bool = Field(True, description="Allow sending messages")
    can_read_conversation: bool = Field(True, description="Allow reading conversations")
    can_read_stats: bool = Field(False, description="Allow reading statistics")
    rate_limit_per_minute: int = Field(60, ge=1, le=1000, description="Rate limit per minute")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    description: Optional[str] = Field(None, description="Description")


class APIKeyUpdate(BaseModel):
    """Schema for updating API key."""
    name: Optional[str] = None
    is_active: Optional[bool] = None
    can_send_message: Optional[bool] = None
    can_read_conversation: Optional[bool] = None
    can_read_stats: Optional[bool] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=1000)
    expires_at: Optional[datetime] = None
    description: Optional[str] = None


class APIKeyResponse(BaseModel):
    """Schema for API key response."""
    id: int
    key: str  # Only shown once upon creation
    name: str
    user_id: Optional[int]
    can_send_message: bool
    can_read_conversation: bool
    can_read_stats: bool
    rate_limit_per_minute: int
    is_active: bool
    expires_at: Optional[datetime]
    description: Optional[str]
    last_used_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyListResponse(BaseModel):
    """Schema for API key list response."""
    keys: list[APIKeyResponse]
    total: int