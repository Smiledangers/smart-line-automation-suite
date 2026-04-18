"""
Webhook schemas for Pydantic models.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl


class WebhookCreate(BaseModel):
    """Schema for creating webhook."""
    name: str = Field(..., description="Name for this webhook")
    user_id: Optional[int] = Field(None, description="Owner user ID")
    url: HttpUrl = Field(..., description="Webhook URL")
    secret: Optional[str] = Field(None, description="Secret for signature")
    event_message_received: bool = Field(True, description="Trigger on message received")
    event_message_sent: bool = Field(False, description="Trigger on message sent")
    event_conversation_started: bool = Field(False, description="Trigger on conversation started")
    event_conversation_ended: bool = Field(False, description="Trigger on conversation ended")
    description: Optional[str] = Field(None, description="Description")


class WebhookUpdate(BaseModel):
    """Schema for updating webhook."""
    name: Optional[str] = None
    url: Optional[HttpUrl] = None
    secret: Optional[str] = None
    event_message_received: Optional[bool] = None
    event_message_sent: Optional[bool] = None
    event_conversation_started: Optional[bool] = None
    event_conversation_ended: Optional[bool] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class WebhookResponse(BaseModel):
    """Schema for webhook response."""
    id: int
    name: str
    user_id: Optional[int]
    url: str
    secret: Optional[str]  # Only shown once upon creation
    event_message_received: bool
    event_message_sent: bool
    event_conversation_started: bool
    event_conversation_ended: bool
    is_active: bool
    last_triggered_at: Optional[datetime]
    last_status_code: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookListResponse(BaseModel):
    """Schema for webhook list response."""
    webhooks: list[WebhookResponse]
    total: int


class WebhookTestResponse(BaseModel):
    """Schema for webhook test response."""
    success: bool
    status_code: Optional[int]
    response_time_ms: Optional[int]
    error: Optional[str]