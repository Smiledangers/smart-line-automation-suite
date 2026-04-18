"""
Telegram Bot Service.
"""
import logging
from typing import Dict, Any, Optional
import httpx
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class TelegramService:
    """Telegram Bot service."""
    
    def __init__(self, token: str = None):
        self.token = token or settings.TELEGRAM_BOT_TOKEN
        self.api_url = f"https://api.telegram.org/bot{self.token}"
    
    async def send_message(
        self,
        chat_id: str,
        text: str,
        message_type: str = "text",
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Send message to Telegram user."""
        async with httpx.AsyncClient() as client:
            # Send text message
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            
            # Add buttons if provided
            if metadata and metadata.get("buttons"):
                payload["reply_markup"] = self._format_buttons(metadata["buttons"])
            
            response = await client.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return {"status": "success", "data": response.json()}
            else:
                logger.error(f"Telegram API error: {response.text}")
                return {"status": "error", "message": response.text}
    
    async def send_photo(
        self,
        chat_id: str,
        photo_url: str,
        caption: str = None
    ) -> Dict[str, Any]:
        """Send photo to Telegram user."""
        async with httpx.AsyncClient() as client:
            payload = {
                "chat_id": chat_id,
                "photo": photo_url
            }
            if caption:
                payload["caption"] = caption
            
            response = await client.post(
                f"{self.api_url}/sendPhoto",
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                return {"status": "success"}
            else:
                return {"status": "error", "message": response.text}
    
    async def send_buttons(
        self,
        chat_id: str,
        text: str,
        buttons: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Send inline buttons to Telegram user."""
        async with httpx.AsyncClient() as client:
            inline_keyboard = [
                [{"text": btn["text"], "callback_data": btn.get("callback_data", btn["text"])}
                for btn in buttons
            ]
            
            payload = {
                "chat_id": chat_id,
                "text": text,
                "reply_markup": {"inline_keyboard": [inline_keyboard]}
            }
            
            response = await client.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=30.0
            )
            
            return response.json()
    
    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle incoming Telegram webhook."""
        message = payload.get("message", {})
        callback_query = payload.get("callback_query", {})
        
        if message:
            return {
                "platform": "telegram",
                "user_id": str(message["from"]["id"]),
                "chat_id": str(message["chat"]["id"]),
                "text": message.get("text", ""),
                "type": "message"
            }
        elif callback_query:
            return {
                "platform": "telegram",
                "user_id": str(callback_query["from"]["id"]),
                "data": callback_query.get("data"),
                "type": "callback"
            }
        
        return {"status": "unknown"}
    
    def _format_buttons(self, buttons: List[Dict]) -> Dict:
        """Format buttons for Telegram inline keyboard."""
        keyboard = []
        for row in buttons:
            keyboard.append([
                {"text": btn["text"], "callback_data": btn.get("action", btn["text"])}
                for btn in row
            ])
        return {"inline_keyboard": keyboard}


# Global service instance
telegram_service = TelegramService()