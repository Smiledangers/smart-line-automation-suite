"""
Webhook endpoints for external notifications.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.webhook import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookListResponse,
    WebhookTestResponse,
)
from app.services.webhook_service import webhook_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("", response_model=WebhookResponse, status_code=201)
async def create_webhook(
    webhook_data: WebhookCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new webhook.
    Note: In production, require admin authentication.
    """
    webhook = await webhook_service.create(
        db=db,
        name=webhook_data.name,
        url=str(webhook_data.url),
        user_id=webhook_data.user_id,
        secret=webhook_data.secret,
        event_message_received=webhook_data.event_message_received,
        event_message_sent=webhook_data.event_message_sent,
        event_conversation_started=webhook_data.event_conversation_started,
        event_conversation_ended=webhook_data.event_conversation_ended,
        description=webhook_data.description,
    )
    return webhook


@router.get("", response_model=WebhookListResponse)
async def list_webhooks(
    skip: int = 0,
    limit: int = 100,
    user_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all webhooks."""
    webhooks, total = await webhook_service.get_all(db, user_id=user_id, skip=skip, limit=limit)
    return {"webhooks": webhooks, "total": total}


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific webhook."""
    webhook = await webhook_service.get_by_id(db, webhook_id)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    webhook_data: WebhookUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a webhook."""
    update_data = webhook_data.model_dump(exclude_unset=True)
    if "url" in update_data:
        update_data["url"] = str(update_data["url"])
    
    webhook = await webhook_service.update(db, webhook_id, **update_data)
    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return webhook


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a webhook."""
    success = await webhook_service.delete(db, webhook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"status": "success", "message": "Webhook deleted"}


@router.post("/{webhook_id}/test", response_model=WebhookTestResponse)
async def test_webhook(
    webhook_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Test a webhook by sending a ping."""
    result = await webhook_service.test_webhook(db, webhook_id)
    return result