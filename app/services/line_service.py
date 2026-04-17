"""LINE service layer for LINE Bot integration."""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.line_user import LINEUser
from app.schemas.line import LINEUserCreate, LINEUserUpdate
from app.utils.circuit_breaker import line_api_circuit_breaker
from linebot import LineBotApi
from linebot.exceptions import LineBotApiError
from linebot.models import TextSendMessage, FlexSendMessage
from app.core.config import settings

logger = logging.getLogger(__name__)

class LineUserService:
    """Service for LINE user management."""
    
    def get_or_create_line_user(self, db: Session, line_user_id: str) -> LINEUser:
        """Get existing LINE user or create new one."""
        line_user = db.query(LINEUser).filter(LINEUser.line_user_id == line_user_id).first()
        if line_user:
            return line_user
        
        # Create new LINE user
        line_user = LINEUser(line_user_id=line_user_id)
        db.add(line_user)
        db.commit()
        db.refresh(line_user)
        return line_user
    
    def get_line_user(self, db: Session, user_id: int) -> Optional[LINEUser]:
        """Get LINE user by internal user ID."""
        return db.query(LINEUser).filter(LINEUser.user_id == user_id).first()
    
    def update_line_user(self, db: Session, line_user_id: str, user_in: dict) -> Optional[LINEUser]:
        """Update LINE user profile."""
        line_user = db.query(LINEUser).filter(LINEUser.line_user_id == line_user_id).first()
        if not line_user:
            return None
        
        for field, value in user_in.items():
            if hasattr(line_user, field):
                setattr(line_user, field, value)
        
        line_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(line_user)
        return line_user
    
    def delete_line_user(self, db: Session, line_user_id: str) -> bool:
        """Delete LINE user."""
        line_user = db.query(LINEUser).filter(LINEUser.line_user_id == line_user_id).first()
        if not line_user:
            return False
        
        db.delete(line_user)
        db.commit()
        return True

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
            logger.info(f"Sent text message to {to}: {text}")
            return True
        except self.LineBotApiError as e:
            logger.error(f"Failed to send text message to {to}: {e}")
            return False
    
    @line_api_circuit_breaker(fallback_func=lambda to, flex_content: False)
    def send_flex_message(self, to: str, flex_content: dict) -> bool:
        """Send flex message via LINE Bot API (push message)."""
        try:
            self.line_bot_api.push_message(to, FlexSendMessage(alt_text="Flex Message", contents=flex_content))
            logger.info(f"Sent flex message to {to}")
            return True
        except self.LineBotApiError as e:
            logger.error(f"Failed to send flex message to {to}: {e}")
            return False

class LineService:
    """Main LINE service that aggregates sub-services."""
    
    def __init__(self):
        self.user_service = LineUserService()
        self.message_service = LineMessageService()
    
    # Delegate methods for backward compatibility
    def get_or_create_line_user(self, db: Session, line_user_id: str) -> LINEUser:
        return self.user_service.get_or_create_line_user(db, line_user_id)
    
    def get_line_user(self, db: Session, user_id: int) -> Optional[LINEUser]:
        return self.user_service.get_line_user(db, user_id)
    
    def update_line_user(self, db: Session, line_user_id: str, user_in: dict) -> Optional[LINEUser]:
        return self.user_service.update_line_user(db, line_user_id, user_in)
    
    def delete_line_user(self, db: Session, line_user_id: str) -> bool:
        return self.user_service.delete_line_user(db, line_user_id)
    
    def send_text_message(self, line_user_id: str, text: str) -> bool:
        return self.message_service.send_text_message(line_user_id, text)
    
    def send_flex_message(self, line_user_id: str, flex_content: dict) -> bool:
        return self.message_service.send_flex_message(line_user_id, flex_content)

line_service = LineService()