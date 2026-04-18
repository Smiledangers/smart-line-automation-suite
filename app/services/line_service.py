"""LINE service layer with async database support."""
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.Models.line_user import LINEUser
from app.schemas.line_user_user import LINEUserCreate, LINEUserUpdate
from app.utils.circuit_breaker import line_api_circuit_breaker
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import (
    TextSendMessage,
    FlexSendMessage,
    TemplateSendMessage,
    ButtonsTemplate,
    MessageTemplateAction,
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class LineUserService:
    """Service for LINE user management."""

    async def get_or_create_line_user(
        self, db: AsyncSession, line_user_id: str
    ) -> LINEUser:
        """Get existing LINE user or create new one."""
        result = await db.execute(
            select(LINEUser).where(LINEUser.line_user_id == line_user_id)
        )
        line_user = result.scalar_one_or_none()
        if line_user:
            return line_user

        # Create new LINE user
        line_user = LINEUser(line_user_id=line_user_id)
        db.add(line_user)
        await db.commit()
        await db.refresh(line_user)
        logger.info(f"Created new LINE user: {line_user_id}")
        return line_user

    async def get_line_user(
        self, db: AsyncSession, user_id: int
    ) -> Optional[LINEUser]:
        """Get LINE user by internal user ID."""
        result = await db.execute(
            select(LINEUser).where(LINEUser.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_line_user_by_line_id(
        self, db: AsyncSession, line_user_id: str
    ) -> Optional[LINEUser]:
        """Get LINE user by LINE ID."""
        result = await db.execute(
            select(LINEUser).where(LINEUser.line_user_id == line_user_id)
        )
        return result.scalar_one_or_none()

    async def update_line_user(
        self, db: AsyncSession, line_user_id: str, user_data: dict
    ) -> Optional[LINEUser]:
        """Update LINE user profile."""
        result = await db.execute(
            select(LINEUser).where(LINEUser.line_user_id == line_user_id)
        )
        line_user = result.scalar_one_or_none()
        if not line_user:
            return None

        for field, value in user_data.items():
            if hasattr(line_user, field):
                setattr(line_user, field, value)

        line_user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(line_user)
        return line_user

    async def delete_line_user(
        self, db: AsyncSession, line_user_id: str
    ) -> bool:
        """Delete LINE user."""
        result = await db.execute(
            select(LINEUser).where(LINEUser.line_user_id == line_user_id)
        )
        line_user = result.scalar_one_or_none()
        if not line_user:
            return False

        await db.delete(line_user)
        await db.commit()
        return True

    async def get_all_line_users(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[LINEUser]:
        """Get all LINE users with pagination."""
        result = await db.execute(select(LINEUser).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def count_line_users(self, db: AsyncSession) -> int:
        """Count total LINE users."""
        from sqlalchemy import func

        result = await db.execute(select(func.count(LINEUser.id)))
        return result.scalar() or 0


class LineMessageService:
    """Service for LINE messaging operations."""

    def __init__(self):
        self.line_bot_api = LineBotApi(settings.LINE_CHANNEL_ACCESS_TOKEN)
        self.LineBotApiError = LineBotApiError

    @line_api_circuit_breaker(fallback_func=lambda to, text: False)
    def send_text_message(self, to: str, text: str) -> bool:
        """Send text message via LINE Bot API (push message)."""
        try:
            self.line_bot_api.push_message(to, TextSendMessage(text=text))
            logger.info(f"Sent text message to {to}: {text[:50]}...")
            return True
        except self.LineBotApiError as e:
            logger.error(f"Failed to send text message to {to}: {e}")
            return False

    @line_api_circuit_breaker(fallback_func=lambda to, flex_content: False)
    def send_flex_message(self, to: str, flex_content: dict) -> bool:
        """Send flex message via LINE Bot API (push message)."""
        try:
            self.line_bot_api.push_message(
                to,
                FlexSendMessage(alt_text="Flex Message", contents=flex_content),
            )
            logger.info(f"Sent flex message to {to}")
            return True
        except self.LineBotApiError as e:
            logger.error(f"Failed to send flex message to {to}: {e}")
            return False

    def send_button_message(
        self,
        to: str,
        title: str,
        text: str,
        actions: List[Dict[str, str]],
    ) -> bool:
        """Send button template message."""
        try:
            template_actions = [
                MessageTemplateAction(label=a["label"], text=a.get("text"), uri=a.get("uri"))
                for a in actions
            ]
            self.line_bot_api.push_message(
                to,
                TemplateSendMessage(
                    alt_text=title,
                    template=ButtonsTemplate(
                        title=title, text=text, actions=template_actions
                    ),
                ),
            )
            logger.info(f"Sent button message to {to}")
            return True
        except self.LineBotApiError as e:
            logger.error(f"Failed to send button message to {to}: {e}")
            return False

    def send_reply_message(self, reply_token: str, text: str) -> bool:
        """Send reply message using reply token."""
        try:
            self.line_bot_api.reply_message(reply_token, TextSendMessage(text=text))
            logger.info(f"Sent reply message: {text[:50]}...")
            return True
        except self.LineBotApiError as e:
            logger.error(f"Failed to send reply message: {e}")
            return False

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get LINE user profile."""
        try:
            profile = self.line_bot_api.get_profile(user_id)
            return {
                "user_id": profile.user_id,
                "display_name": profile.display_name,
                "picture_url": profile.picture_url,
                "status_message": profile.status_message,
            }
        except self.LineBotApiError as e:
            logger.error(f"Failed to get profile for {user_id}: {e}")
            return None


class LineService:
    """Main LINE service that aggregates sub-services."""

    def __init__(self):
        self.user_service = LineUserService()
        self.message_service = LineMessageService()

    # Delegate methods for backward compatibility
    async def get_or_create_line_user(
        self, db: AsyncSession, line_user_id: str
    ) -> LINEUser:
        return await self.user_service.get_or_create_line_user(db, line_user_id)

    async def get_line_user(
        self, db: AsyncSession, user_id: int
    ) -> Optional[LINEUser]:
        return await self.user_service.get_line_user(db, user_id)

    async def get_line_user_by_line_id(
        self, db: AsyncSession, line_user_id: str
    ) -> Optional[LINEUser]:
        return await self.user_service.get_line_user_by_line_id(db, line_user_id)

    async def update_line_user(
        self, db: AsyncSession, line_user_id: str, user_data: dict
    ) -> Optional[LINEUser]:
        return await self.user_service.update_line_user(db, line_user_id, user_data)

    async def delete_line_user(
        self, db: AsyncSession, line_user_id: str
    ) -> bool:
        return await self.user_service.delete_line_user(db, line_user_id)

    async def get_all_line_users(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[LINEUser]:
        return await self.user_service.get_all_line_users(db, skip, limit)

    def send_text_message(self, line_user_id: str, text: str) -> bool:
        return self.message_service.send_text_message(line_user_id, text)

    def send_flex_message(self, line_user_id: str, flex_content: dict) -> bool:
        return self.message_service.send_flex_message(line_user_id, flex_content)

    def send_button_message(
        self,
        line_user_id: str,
        title: str,
        text: str,
        actions: List[Dict[str, str]],
    ) -> bool:
        return self.message_service.send_button_message(line_user_id, title, text, actions)

    def send_reply_message(self, reply_token: str, text: str) -> bool:
        return self.message_service.send_reply_message(reply_token, text)

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        return self.message_service.get_profile(user_id)


line_service = LineService()