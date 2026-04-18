"""
Telegram Bot API endpoints.
"""
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.services.telegram_service import telegram_service
from app.services.unified_messaging import unified_message_service, Platform, MessageType
from app.core.config import get_settings
from app.core.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/telegram/", tags=["telegram"])
settings = get_settings()


class TelegramSendRequest(BaseModel):
    """Request to send Telegram message."""
    chat_id: str
    message: str
    buttons: Optional[list] = None


class TelegramCallbackRequest(BaseModel):
    """Webhook callback from Telegram."""
    update_id: int
    message: Optional[dict] = None
    edited_message: Optional[dict] = None
    callback_query: Optional[dict] = None


@router.post("/send")
async def send_telegram_message(
    request: TelegramSendRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Send message to Telegram user."""
    result = await telegram_service.send_message(
        request.chat_id,
        request.message,
        metadata={"buttons": request.buttons} if request.buttons else None,
    )
    return result


@router.post("/webhook")
async def telegram_webhook(
    request: TelegramCallbackRequest,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, str]:
    """Handle incoming Telegram updates."""
    if request.message:
        user_id = str(request.message.get("from", {}).get("id"))
        text = request.message.get("text")
        
        if user_id and text:
            await telegram_service.handle_incoming_message(db, user_id, text)
    
    return {"status": "ok"}


@router.get("/health")
async def telegram_health():
    """Telegram service health check."""
    return {
        "status": "healthy",
        "platform": "telegram",
        "configured": bool(settings.TELEGRAM_BOT_TOKEN),
    }