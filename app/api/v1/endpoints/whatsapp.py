"""
WhatsApp Business API endpoints with Meta webhooks.
"""
import logging
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.services.unified_messaging import UnifiedMessageService, Platform

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])


class WhatsAppMessageRequest(BaseModel):
    """WhatsApp incoming message."""
    from_number: str
    message_id: str
    message_type: str  # text, image, audio, video, document
    content: str
    timestamp: Optional[str] = None


class WhatsAppSendRequest(BaseModel):
    """Request to send WhatsApp message."""
    to: str
    message: str
    message_type: str = "text"


class WhatsAppCallbackRequest(BaseModel):
    """Webhook callback from WhatsApp Business API."""
    entry: list[Dict[Any, Any]]


# Initialize unified messaging service
unified_service = UnifiedMessageService()


@router.get("/webhook")
async def verify_webhook(
    hub_mode: str,
    hub_verify_token: str,
    hub_challenge: str,
):
    """
    Verify webhook for WhatsApp (Meta).
    Setup: Set VERIFY_TOKEN in .env to match Meta's verification.
    """
    from app.core.config import get_settings
    settings = get_settings()
    
    expected_token = getattr(settings, 'WHATSAPP_VERIFY_TOKEN', 'your_verify_token')
    
    if hub_mode == "subscribe" and hub_verify_token == expected_token:
        logger.info("WhatsApp webhook verified")
        return hub_challenge
    
    raise HTTPException(status_code=403, detail="Invalid verify token")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Receive incoming messages and status updates from WhatsApp Business API.
    
    Payload format from Meta:
    {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {...},
                    "messages": [...],
                    "statuses": [...]
                },
                "field": "messages"
            }]
        }]
    }
    """
    body = await request.json()
    logger.info(f"WhatsApp webhook received: {body}")
    
    try:
        entry = body.get("entry", [])
        
        for e in entry:
            changes = e.get("changes", [])
            
            for change in changes:
                value = change.get("value", {})
                
                # Handle incoming messages
                messages = value.get("messages", [])
                for msg in messages:
                    await _handle_incoming_message(db, msg, value.get("metadata", {}))
                
                # Handle status updates (sent, delivered, read, failed)
                statuses = value.get("statuses", [])
                for status in statuses:
                    await _handle_status_update(db, status)
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_incoming_message(
    db: AsyncSession,
    msg: Dict[Any, Any],
    metadata: Dict[Any, Any],
):
    """Process incoming WhatsApp message."""
    from app.Models.line_user import LINEUser
    from app.schemas.line_user import LINEUserCreate
    from app.services.line_service import line_service
    
    # Extract message details
    from_id = msg.get("from", "")
    msg_id = msg.get("id", "")
    timestamp = msg.get("timestamp")
    
    # Get message content
    text = None
    msg_type = msg.get("type", "text")
    
    if msg_type == "text":
        text = msg.get("text", {}).get("body", "")
    elif msg_type == "image":
        text = "[Image]"
    elif msg_type == "audio":
        text = "[Audio]"
    elif msg_type == "video":
        text = "[Video]"
    elif msg_type == "document":
        doc = msg.get("document", {})
        text = f"[Document: {doc.get('filename', 'file')}]"
    elif msg_type == "location":
        loc = msg.get("location", {})
        text = f"[Location: {loc.get('latitude')}, {loc.get('longitude')}]"
    
    if not text:
        return
    
    # Create or get user
    user = await line_service.get_or_create_line_user(db, f"whatsapp:{from_id}")
    
    # Update profile with WhatsApp info
    profile_data = {
        "display_name": f"WhatsApp {from_id[-4:]}",
        "platform": "whatsapp",
    }
    await line_service.update_line_user(db, f"whatsapp:{from_id}", profile_data)
    
    logger.info(f"WhatsApp message from {from_id}: {text[:50]}...")
    
    # TODO: Trigger AI processing or webhook notification here
    # For now, store the message
    
    # Optionally trigger webhooks
    try:
        from app.services.webhook_service import webhook_service
        await webhook_service.trigger(
            db,
            "message_received",
            {
                "platform": "whatsapp",
                "user_id": from_id,
                "message_id": msg_id,
                "message_type": msg_type,
                "content": text,
                "timestamp": timestamp,
            }
        )
    except Exception as e:
        logger.warning(f"Webhook trigger failed: {e}")


async def _handle_status_update(db: AsyncSession, status: Dict[Any, Any]):
    """Process message status updates."""
    msg_id = status.get("id", "")
    status_type = status.get("status", "")  # sent, delivered, read, failed
    recipient = status.get("to", "")
    
    logger.info(f"WhatsApp message {msg_id} status: {status_type} -> {recipient}")
    
    # TODO: Update message status in database
    # TODO: Trigger webhook for status changes


@router.post("/send")
async def send_message(
    message: WhatsAppSendRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to WhatsApp user via Business API.
    
    Note: Requires WhatsApp Business API setup with Meta.
    """
    from app.core.config import get_settings
    settings = get_settings()
    
    # Check if WhatsApp is configured
    whatsapp_phone_number_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None)
    whatsapp_access_token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', None)
    
    if not whatsapp_phone_number_id or not whatsapp_access_token:
        # Fallback to unified messaging if configured
        if Platform.WHATSAPP in unified_service.platforms:
            result = await unified_service.send_message(
                Platform.WHATSAPP,
                message.to,
                message.message,
            )
            return result
        
        raise HTTPException(
            status_code=503,
            detail="WhatsApp not configured. Set WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ACCESS_TOKEN in .env"
        )
    
    # Send via WhatsApp Business API
    import httpx
    
    url = f"https://graph.facebook.com/v18.0/{whatsapp_phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {whatsapp_access_token}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": message.to,
        "type": "text",
        "text": {"body": message.message},
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "status": "success",
                    "message_id": result.get("messages", [{}])[0].get("id"),
                }
            else:
                logger.error(f"WhatsApp API error: {response.text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"WhatsApp API error: {response.text}"
                )
    except Exception as e:
        logger.error(f"WhatsApp send error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def whatsapp_health():
    """WhatsApp service health check."""
    from app.core.config import get_settings
    settings = get_settings()
    
    configured = bool(
        getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', None) and
        getattr(settings, 'WHATSAPP_ACCESS_TOKEN', None)
    )
    
    return {
        "status": "healthy" if configured else "not_configured",
        "platform": "whatsapp",
        "configured": configured,
    }