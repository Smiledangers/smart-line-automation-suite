"""
LINE Bot endpoints.
"""
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
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.services.line_service import line_service
from app.tasks.ai_tasks import process_line_message

router = APIRouter()

# LINE Bot API objects
line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)


@router.post("/webhook")
async def callback(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    LINE webhook endpoint.
    """
    signature = request.headers["X-Line-Signature"]
    body = await request.body()
    body = body.decode("utf-8")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    return "OK"


@handler.add(FollowEvent)
def handle_follow(event):
    """Handle when user follows the bot."""
    user_id = event.source.user_id
    # Get or create user in DB
    line_service.get_or_create_line_user(user_id, db)
    # Send welcome message
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="您好！歡迎使用智慧 LINE Bot。我可以協助您查詢資訊、執行任務等等。"),
    )


@handler.add(UnfollowEvent)
def handle_unfollow(event):
    """Handle when user unfollows the bot."""
    user_id = event.source.user_id
    # TODO: Handle user unfollow (e.g., mark as inactive)
    pass


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """Handle text messages from users."""
    user_id = event.source.user_id
    message_text = event.message.text

    # Process message asynchronously using Celery
    background_tasks.add_task(process_line_message, user_id, message_text)

    # Optional: Send immediate acknowledgment
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="我收到了您的訊息，正在處理中..."),
    )


@handler.add(PostbackEvent)
def handle_postback(event):
    """Handle postback events from buttons, etc."""
    user_id = event.source.user_id
    data = event.postback.data
    # TODO: Handle postback data
    pass