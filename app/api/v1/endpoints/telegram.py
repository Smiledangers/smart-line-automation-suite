"""
Telegram Bot API endpoints.
"""
import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel

from app.services.telegram_service import telegram_service
from app.services.unified_messaging import unified_message_service, Platform, MessageType
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix=\"/telegram\", tags=[\"telegram\"])
settings = get_settings()


class TelegramSendRequest(BaseModel):
    """Request to send Telegram message."""
    chat_id: str
    message: str
    buttons: list = None


class TelegramCallbackRequest(BaseModel):
    """Webhook callback from Telegram."""
    update_id: int
    message: dict = None
    callback_query: dict = None


@router.post(\"/send\")
async def send_telegram_message(request: TelegramSendRequest) -> Dict[str, Any]:
    """
    Send message to Telegram user.
    """
    result = await telegram_service.send_message(
        chat_id=request.chat_id,
        text=request.message,
        message_type=\"text\",
        metadata={\"buttons\": request.buttons} if request.buttons else None
    )
    return result


@router.post(\"/send_photo\")
async def send_telegram_photo(
    chat_id: str = Body(...),
    photo_url: str = Body(...),
    caption: str = Body(None)
) -> Dict[str, Any]:
    """
    Send photo to Telegram user.
    """
    result = await telegram_service.send_photo(
        chat_id=chat_id,
        photo_url=photo_url,
        caption=caption
    )
    return result


@router.post(\"/webhook\")
async def telegram_webhook(request: dict = Body(...)) -> Dict[str, Any]:
    """
    Handle Telegram webhook callbacks.
    """
    result = await telegram_service.handle_webhook(request)
    return result


@router.get(\"/status\")
async def telegram_status() -> Dict[str, Any]:
    """
    Get Telegram bot status.
    """
    return {
        \"status\": \"active\",
        \"platform\": \"telegram\",
        \"configured\": bool(settings.TELEGRAM_BOT_TOKEN != \"your-telegram-bot-token\")
    }


@router.post(\"/broadcast\")
async def broadcast_to_telegram(
    chat_ids: list = Body(...),
    message: str = Body(...)
) -> Dict[str, Any]:
    """
    Broadcast message to multiple Telegram users.
    """
    results = []
    for chat_id in chat_ids:
        result = await telegram_service.send_message(chat_id, message)
        results.append(result)
    
    return {
        \"status\": \"success\",
        \"sent\": len(results),
        \"results\": results
    }