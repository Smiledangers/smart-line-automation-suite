"""
LINE Bot endpoints with async database support.
"""
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent,
    TextMessage,
    TextSendMessage,
    FollowEvent,
    UnfollowEvent,
    JoinEvent,
    LeaveEvent,
    PostbackEvent,
)
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.config import settings, get_settings
from app.core.database import get_db
from app.services.line_service import line_service
from app.tasks.ai_tasks import process_line_message

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter()

# LINE Bot API objects
line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)


# Request/Response models
class WebhookResponse(BaseModel):
    """Webhook response model."""
    message: str = "OK"


class FollowRequest(BaseModel):
    """Follow event data."""
    user_id: str
    display_name: Optional[str] = None
    picture_url: Optional[str] = None


class MessageRequest(BaseModel):
    """Message event data."""
    user_id: str
    message: str
    reply_token: Optional[str] = None


class PostbackRequest(BaseModel):
    """Postback event data."""
    user_id: str
    data: str
    reply_token: Optional[str] = None


@router.post("/webhook", response_model=WebhookResponse)
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> WebhookResponse:
    """
    LINE webhook endpoint for receiving events.
    
    Handles:
    - FollowEvent: User follows the bot
    - UnfollowEvent: User unfollows the bot
    - MessageEvent: User sends a message
    - PostbackEvent: User clicks a button/postback
    """
    signature = request.headers.get("X-Line-Signature", "")
    body = await request.body()
    body_str = body.decode("utf-8")

    logger.info(f"Received LINE webhook: {body_str[:100]}...")

    try:
        handler.handle(body_str, signature)
    except InvalidSignatureError:
        logger.warning("Invalid signature received")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return WebhookResponse(message="OK")


@router.post("/follow")
async def follow(
    follow_data: FollowRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Handle follow event (for manual triggering or testing).
    """
    try:
        # Get or create LINE user
        line_user = await line_service.get_or_create_line_user(
            db, follow_data.user_id
        )
        
        # Update profile if provided
        if follow_data.display_name:
            await line_service.update_line_user(
                db,
                follow_data.user_id,
                {"display_name": follow_data.display_name, "is_followed": True},
            )
        
        logger.info(f"User {follow_data.user_id} followed the bot")
        
        return {
            "status": "success",
            "message": "User followed",
            "line_user_id": line_user.id,
        }
    except Exception as e:
        logger.error(f"Error handling follow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/unfollow")
async def unfollow(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Handle unfollow event (for manual triggering or testing).
    """
    try:
        # Update LINE user as not followed
        result = await line_service.update_line_user(
            db, user_id, {"is_followed": False}
        )
        
        if result:
            logger.info(f"User {user_id} unfollowed the bot")
            return {"status": "success", "message": "User unfollowed"}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling unfollow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/message")
async def message(
    message_data: MessageRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Handle message event (for manual triggering or testing).
    """
    try:
        # Get or create LINE user
        line_user = await line_service.get_or_create_line_user(
            db, message_data.user_id
        )
        
        # Process message asynchronously
        background_tasks.add_task(
            process_line_message, message_data.user_id, message_data.message
        )
        
        logger.info(f"Message processed for user {message_data.user_id}")
        
        return {
            "status": "success",
            "message": "Message received",
            "reply": "我收到了您的訊息，正在處理中...",
        }
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/postback")
async def postback(
    postback_data: PostbackRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Handle postback event (for button clicks, rich menu, etc.).
    """
    try:
        logger.info(f"Postback received: {postback_data.data} from {postback_data.user_id}")
        
        # Process postback data based on content
        response_message = await _handle_postback_data(
            db, postback_data.user_id, postback_data.data
        )
        
        return {
            "status": "success",
            "message": response_message,
        }
    except Exception as e:
        logger.error(f"Error handling postback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def _handle_postback_data(db: AsyncSession, user_id: str, data: str) -> str:
    """
    Process postback data and return appropriate response.
    """
    # Example postback handling
    if data.startswith("action="):
        action = data.split("=")[1]
        
        if action == "help":
            return "請告訴我能幫您什麼？"
        elif action == "status":
            return "系統運作正常！"
        elif action == "menu":
            return "這是選單選項..."
        else:
            return "收到您的選擇"
    
    return "感謝您的回應"


# Legacy handler functions (for webhook handler compatibility)
@handler.add(FollowEvent)
def handle_follow(event):
    """Handle when user follows the bot."""
    user_id = event.source.user_id
    logger.info(f"User {user_id} followed the bot")
    
    try:
        # Send welcome message
        line_service.message_service.reply_message(
            event.reply_token,
            TextSendMessage(
                text="您好！歡迎使用智慧 LINE Bot 🎉\n\n"
                     "我可以協助您：\n"
                     "• 查詢資訊\n"
                     "• 執行自動化任務\n"
                     "• AI 對話\n"
                     "• 更多功能...\n\n"
                     "請告訴我能為您做什麼？"
            ),
        )
    except Exception as e:
        logger.error(f"Error sending welcome message: {e}")


@handler.add(UnfollowEvent)
def handle_unfollow(event):
    """Handle when user unfollows the bot."""
    user_id = event.source.user_id
    logger.info(f"User {user_id} unfollowed the bot")
    # Note: In production, you might want to mark the user as inactive in the database
    # This requires async database access, which the webhook handler doesn't support directly


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """Handle text messages from users."""
    user_id = event.source.user_id
    message_text = event.message.text
    
    logger.info(f"Message from {user_id}: {message_text}")
    
    # Send acknowledgment
    try:
        line_service.message_service.reply_message(
            event.reply_token,
            TextSendMessage(text="我收到了您的訊息，正在處理中... 🔄"),
        )
    except Exception as e:
        logger.error(f"Error sending acknowledgment: {e}")


@handler.add(PostbackEvent)
def handle_postback(event):
    """Handle postback events from buttons, rich menu, etc."""
    user_id = event.source.user_id
    postback_data = event.postback.data
    
    logger.info(f"Postback from {user_id}: {postback_data}")
    
    try:
        # Determine response based on postback data
        response_text = "感謝您的回應！"
        
        if "help" in postback_data:
            response_text = "需要幫助嗎？請告訴我您的問題。"
        elif "status" in postback_data:
            response_text = "系統狀態：正常運作中 ✅"
        
        line_service.message_service.reply_message(
            event.reply_token,
            TextSendMessage(text=response_text),
        )
    except Exception as e:
        logger.error(f"Error handling postback: {e}")


# Additional endpoints for LINE Login
@router.get("/profile/{user_id}")
async def get_profile(
    user_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get LINE user profile.
    """
    try:
        profile = line_service.get_profile(user_id)
        if profile:
            return {"status": "success", "profile": profile}
        else:
            raise HTTPException(status_code=404, detail="User not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users")
async def list_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List all LINE users.
    """
    try:
        users = await line_service.get_all_line_users(db, skip, limit)
        return {
            "status": "success",
            "users": [
                {
                    "id": u.id,
                    "line_user_id": u.line_user_id,
                    "display_name": u.display_name,
                    "is_followed": u.is_followed,
                    "created_at": u.created_at.isoformat() if u.created_at else None,
                }
                for u in users
            ],
        }
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))