"""
Unified Messaging Service - supports LINE, Telegram, WhatsApp, Discord, etc.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported messaging platforms."""
    LINE = "line"
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    DISCORD = "discord"
    FACEBOOK = "facebook"


class MessageType(Enum):
    """Message types."""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    STICKER = "sticker"
    BUTTONS = "buttons"
    CAROUSEL = "carousel"


class UnifiedMessageService:
    """
    Unified messaging service for all platforms.
    Send once, deliver everywhere.
    """
    
    def __init__(self):
        self.platforms: Dict[Platform, Any] = {}
    
    def register_platform(self, platform: Platform, handler: Any):
        """Register a platform handler."""
        self.platforms[platform] = handler
        logger.info(f"Registered platform: {platform.value}")
    
    async def send_message(
        self,
        platform: Platform,
        user_id: str,
        message: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Send message to a specific platform."""
        if platform not in self.platforms:
            return {"status": "error", "message": f"Platform {platform.value} not registered"}
        
        handler = self.platforms[platform]
        
        try:
            if platform == Platform.LINE:
                return await handler.send_line_message(user_id, message, message_type, metadata)
            elif platform == Platform.TELEGRAM:
                return await handler.send_telegram_message(user_id, message, message_type, metadata)
            elif platform == Platform.WHATSAPP:
                return await handler.send_whatsapp_message(user_id, message, message_type, metadata)
            elif platform == Platform.DISCORD:
                return await handler.send_discord_message(user_id, message, message_type, metadata)
            else:
                return {"status": "error", "message": "Platform not supported"}
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {"status": "error", "message": str(e)}
    
    async def broadcast(
        self,
        message: str,
        user_ids_by_platform: Dict[Platform, List[str]],
        message_type: MessageType = MessageType.TEXT
    ) -> Dict[str, Any]:
        """Broadcast message to multiple platforms."""
        results = {}
        
        for platform, user_ids in user_ids_by_platform.items():
            platform_results = []
            for user_id in user_ids:
                result = await self.send_message(platform, user_id, message, message_type)
                platform_results.append(result)
            results[platform.value] = platform_results
        
        return {"status": "success", "results": results}
    
    async def handle_webhook(self, platform: Platform, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming webhook from any platform."""
        if platform not in self.platforms:
            return {"status": "error", "message": "Platform not registered"}
        
        handler = self.platforms[platform]
        return await handler.handle_webhook(payload)


# Global unified service
unified_message_service = UnifiedMessageService()