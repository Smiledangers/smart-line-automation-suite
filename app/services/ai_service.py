"""AI service layer for LangGraph integration with async support."""
import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from openai import AsyncOpenAI

from app.core.config import get_settings

settings = get_settings()

# Configure structured logging
logger = logging.getLogger(__name__)

# In-memory storage (replace with proper database in production)
_conversation_store: Dict[str, Dict] = {}
_message_store: Dict[str, List[Dict]] = {}


class ConversationManagementService:
    """Service for managing conversations."""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        logger.info("ConversationManagementService initialized")

    async def create_conversation(self, user_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        """Create a new conversation for a user."""
        try:
            conversation_id = str(uuid.uuid4())
            now = datetime.utcnow().isoformat()

            conversation = {
                "id": conversation_id,
                "user_id": user_id,
                "title": title or f"Conversation {now}",
                "created_at": now,
                "updated_at": now,
                "is_active": True,
            }

            _conversation_store[conversation_id] = conversation
            _message_store[conversation_id] = []

            logger.info(f"Conversation created: {conversation_id}")
            return conversation
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise

    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a conversation by ID."""
        return _conversation_store.get(conversation_id)

    async def get_user_conversations(self, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Retrieve conversations for a specific user."""
        user_conversations = [
            conv for conv in _conversation_store.values()
            if conv["user_id"] == user_id and conv["is_active"]
        ]
        user_conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        return user_conversations[offset : offset + limit]


class ChatProcessingService:
    """Service for processing chat messages using LangGraph agents."""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._initialize_agent()
        logger.info("ChatProcessingService initialized")

    def _initialize_agent(self):
        """Placeholder for LangGraph agent initialization."""
        logger.info("LangGraph agent initialization placeholder")

    async def chat(
        self, conversation_id: str, user_message: str, user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a user message and generate a response using LangGraph agents."""
        try:
            conversation = await ConversationManagementService().get_conversation(conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")

            if user_id and conversation["user_id"] != user_id:
                raise ValueError("Unauthorized access to conversation")

            # Add user message to history
            user_msg = {
                "id": str(uuid.uuid4()),
                "role": "user",
                "content": user_message,
                "timestamp": datetime.utcnow().isoformat(),
            }
            _message_store[conversation_id].append(user_msg)

            # Use OpenAI as placeholder (replace with LangGraph agent)
            response = await self.openai_client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    *[
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in _message_store[conversation_id]
                    ],
                ],
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS,
            )

            assistant_message = response.choices[0].message.content

            # Add assistant message to history
            assistant_msg = {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "content": assistant_message,
                "timestamp": datetime.utcnow().isoformat(),
            }
            _message_store[conversation_id].append(assistant_msg)

            # Update conversation timestamp
            conversation["updated_at"] = datetime.utcnow().isoformat()
            _conversation_store[conversation_id] = conversation

            return {
                "message": assistant_message,
                "conversation_id": conversation_id,
                "message_id": assistant_msg["id"],
            }
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Error processing chat: {e}")
            raise


class ConversationHistoryService:
    """Service for retrieving conversation history."""

    def __init__(self):
        logger.info("ConversationHistoryService initialized")

    async def get_conversation_history(
        self, conversation_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve message history for a conversation."""
        if conversation_id not in _conversation_store:
            raise ValueError(f"Conversation {conversation_id} not found")

        messages = _message_store.get(conversation_id, [])
        return messages[offset : offset + limit]


class AIService:
    """Main AI service that aggregates sub-services."""

    def __init__(self):
        self.conversation_service = ConversationManagementService()
        self.chat_service = ChatProcessingService()
        self.history_service = ConversationHistoryService()

    async def create_conversation(self, user_id: str, title: Optional[str] = None) -> Dict[str, Any]:
        return await self.conversation_service.create_conversation(user_id, title)

    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        return await self.conversation_service.get_conversation(conversation_id)

    async def get_user_conversations(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        return await self.conversation_service.get_user_conversations(user_id, limit)

    async def chat(self, conversation_id: str, user_message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        return await self.chat_service.chat(conversation_id, user_message, user_id)

    async def get_conversation_history(
        self, conversation_id: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, Any]]:
        return await self.history_service.get_conversation_history(conversation_id, limit, offset)


ai_service = AIService()