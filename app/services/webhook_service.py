"""
Webhook service for external notifications.
"""
import hashlib
import hmac
import logging
import time
from typing import Optional, List, Dict, Any
from datetime import datetime

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.Models.webhook import Webhook

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for Webhook management."""

    @staticmethod
    async def create(
        db: AsyncSession,
        name: str,
        url: str,
        user_id: Optional[int] = None,
        secret: Optional[str] = None,
        event_message_received: bool = True,
        event_message_sent: bool = False,
        event_conversation_started: bool = False,
        event_conversation_ended: bool = False,
        description: Optional[str] = None,
    ) -> Webhook:
        """Create a new webhook."""
        webhook = Webhook(
            name=name,
            url=url,
            user_id=user_id,
            secret=secret,
            event_message_received=event_message_received,
            event_message_sent=event_message_sent,
            event_conversation_started=event_conversation_started,
            event_conversation_ended=event_conversation_ended,
            description=description,
        )
        
        db.add(webhook)
        await db.commit()
        await db.refresh(webhook)
        
        logger.info(f"Created webhook: {name}")
        return webhook

    @staticmethod
    async def get_by_id(db: AsyncSession, webhook_id: int) -> Optional[Webhook]:
        """Get webhook by ID."""
        result = await db.execute(select(Webhook).where(Webhook.id == webhook_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Webhook], int]:
        """Get all webhooks."""
        query = select(Webhook)
        count_query = select(Webhook)
        
        if user_id:
            query = query.where(Webhook.user_id == user_id)
            count_query = count_query.where(Webhook.user_id == user_id)
        
        query = query.offset(skip).limit(limit).order_by(Webhook.created_at.desc())
        
        result = await db.execute(query)
        webhooks = result.scalars().all()
        
        count_result = await db.execute(count_query)
        total = len(count_result.scalars().all())
        
        return list(webhooks), total

    @staticmethod
    async def update(
        db: AsyncSession,
        webhook_id: int,
        **kwargs,
    ) -> Optional[Webhook]:
        """Update a webhook."""
        webhook = await WebhookService.get_by_id(db, webhook_id)
        if not webhook:
            return None
        
        for key, value in kwargs.items():
            if hasattr(webhook, key) and value is not None:
                setattr(webhook, key, value)
        
        webhook.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(webhook)
        
        logger.info(f"Updated webhook: {webhook.name}")
        return webhook

    @staticmethod
    async def delete(db: AsyncSession, webhook_id: int) -> bool:
        """Delete a webhook."""
        webhook = await WebhookService.get_by_id(db, webhook_id)
        if not webhook:
            return False
        
        await db.delete(webhook)
        await db.commit()
        
        logger.info(f"Deleted webhook: {webhook.name}")
        return True

    @staticmethod
    async def trigger(
        db: AsyncSession,
        event: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Trigger webhooks for an event."""
        # Get active webhooks that listen to this event
        event_field = f"event_{event}"
        
        if not hasattr(Webhook, event_field):
            return {"status": "error", "message": f"Unknown event: {event}"}
        
        query = select(Webhook).where(Webhook.is_active == True)
        result = await db.execute(query)
        webhooks = result.scalars().all()
        
        # Filter webhooks that care about this event
        triggered = []
        for webhook in webhooks:
            if getattr(webhook, event_field, False):
                # Trigger this webhook
                success, status_code, error = await WebhookService._send_webhook(
                    webhook.url,
                    webhook.secret,
                    event,
                    payload,
                )
                
                # Update last triggered
                webhook.last_triggered_at = datetime.utcnow()
                webhook.last_status_code = status_code
                await db.commit()
                
                triggered.append({
                    "webhook_id": webhook.id,
                    "name": webhook.name,
                    "success": success,
                    "status_code": status_code,
                })
                
                if not success:
                    logger.warning(f"Webhook {webhook.name} failed: {error}")
        
        return {
            "status": "success",
            "triggered": len(triggered),
            "results": triggered,
        }

    @staticmethod
    async def _send_webhook(
        url: str,
        secret: Optional[str],
        event: str,
        payload: Dict[str, Any],
    ) -> tuple[bool, Optional[int], Optional[str]]:
        """Send webhook request."""
        start_time = time.time()
        
        # Prepare payload
        payload_with_event = {
            "event": event,
            "timestamp": datetime.utcnow().isoformat(),
            "data": payload,
        }
        
        # Generate signature if secret is provided
        headers = {"Content-Type": "application/json"}
        if secret:
            import json
            body = json.dumps(payload_with_event)
            signature = hmac.new(
                secret.encode(),
                body.encode(),
                hashlib.sha256,
            ).hexdigest()
            headers["X-Webhook-Signature"] = signature
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload_with_event,
                    headers=headers,
                    timeout=30.0,
                )
                
                elapsed_ms = int((time.time() - start_time) * 1000)
                logger.info(f"Webhook triggered: {url} - {response.status_code} ({elapsed_ms}ms)")
                
                return response.status_code < 400, response.status_code, None
                
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return False, None, str(e)

    @staticmethod
    async def test_webhook(db: AsyncSession, webhook_id: int) -> Dict[str, Any]:
        """Test a webhook by sending a ping."""
        webhook = await WebhookService.get_by_id(db, webhook_id)
        if not webhook:
            return {"success": False, "error": "Webhook not found"}
        
        success, status_code, error = await WebhookService._send_webhook(
            webhook.url,
            webhook.secret,
            "test",
            {"test": True, "message": "This is a test ping"},
        )
        
        # Update last triggered
        webhook.last_triggered_at = datetime.utcnow()
        webhook.last_status_code = status_code
        await db.commit()
        
        return {
            "success": success,
            "status_code": status_code,
            "error": error,
        }


webhook_service = WebhookService()