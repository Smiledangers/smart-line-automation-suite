"""AI service layer with database integration."""
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from openai import AsyncOpenAI

from app.core.config import get_settings
from app.Models.ai_conversation import AIConversation, AIMessage
from app.utils.circuit_breaker import llm_invoke_circuit_breaker

settings = get_settings()

logger = logging.getLogger(__name__)


class ConversationManagementService:
    """Service for managing AI conversations."""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def create_conversation(
        self, db: AsyncSession, user_id: int, title: Optional[str] = None
    ) -> AIConversation:
        """Create a new conversation for a user."""
        conversation = AIConversation(
            user_id=user_id,
            title=title or f"Conversation {datetime.utcnow().isoformat()}",
            model=settings.OPENAI_MODEL,
            is_active=True,
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        logger.info(f"Conversation created: {conversation.id}")
        return conversation

    async def get_conversation(
        self, db: AsyncSession, conversation_id: int
    ) -> Optional[AIConversation]:
        """Get a conversation by ID."""
        result = await db.execute(
            select(AIConversation).where(AIConversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_user_conversations(
        self, db: AsyncSession, user_id: int, limit: int = 50, offset: int = 0
    ) -> List[AIConversation]:
        """Get all conversations for a user."""
        result = await db.execute(
            select(AIConversation)
            .where(
                AIConversation.user_id == user_id,
                AIConversation.is_active == True,
            )
            .order_by(AIConversation.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_user_conversations(self, db: AsyncSession, user_id: int) -> int:
        """Count total conversations for a user."""
        result = await db.execute(
            select(func.count(AIConversation.id)).where(
                AIConversation.user_id == user_id, AIConversation.is_active == True
            )
        )
        return result.scalar() or 0

    async def delete_conversation(
        self, db: AsyncSession, conversation_id: int
    ) -> bool:
        """Soft delete a conversation."""
        conversation = await self.get_conversation(db, conversation_id)
        if conversation:
            conversation.is_active = False
            await db.commit()
            return True
        return False


class ChatProcessingService:
    """Service for processing chat messages."""

    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize LangGraph agent placeholder."""
        logger.info("LangGraph agent placeholder initialized")

    async def chat(
        self,
        db: AsyncSession,
        user_id: int,
        message: str,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Process a chat message and return AI response."""
        # Get or create conversation
        if conversation_id:
            conv_service = ConversationManagementService()
            conversation = await conv_service.get_conversation(db, conversation_id)
            if not conversation:
                raise ValueError(f"Conversation {conversation_id} not found")
            if conversation.user_id != user_id:
                raise ValueError("Unauthorized access to conversation")
        else:
            conv_service = ConversationManagementService()
            conversation = await conv_service.create_conversation(
                db, user_id, f"Chat {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
            )

        # Save user message
        user_message = AIMessage(
            conversation_id=conversation.id,
            role="user",
            content=message,
        )
        db.add(user_message)
        await db.commit()

        # Get conversation history
        history = await self._get_conversation_history(db, conversation.id)

        # Generate AI response with circuit breaker
        try:
            response = await circuit_breaker.call(
                self._generate_response, message, history
            )
        except Exception as e:
            logger.error(f"AI response generation failed: {e}")
            raise

        # Save AI response
        ai_message = AIMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=response,
        )
        db.add(ai_message)

        # Update conversation
        conversation.updated_at = datetime.utcnow()
        await db.commit()

        return {
            "message": response,
            "conversation_id": conversation.id,
            "message_id": ai_message.id,
        }

    async def _generate_response(
        self, message: str, history: List[Dict]
    ) -> str:
        """Generate response using OpenAI."""
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."}
        ]

        # Add history
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current message
        messages.append({"role": "user", "content": message})

        response = await self.openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            temperature=settings.OPENAI_TEMPERATURE,
            max_tokens=settings.OPENAI_MAX_TOKENS,
        )

        return response.choices[0].message.content

    async def _get_conversation_history(
        self, db: AsyncSession, conversation_id: int, limit: int = 20
    ) -> List[Dict]:
        """Get conversation message history."""
        result = await db.execute(
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation_id)
            .order_by(AIMessage.created_at)
            .limit(limit)
        )
        messages = result.scalars().all()
        return [{"role": m.role, "content": m.content} for m in messages]


class ConversationHistoryService:
    """Service for retrieving conversation history."""

    async def get_conversation_history(
        self,
        db: AsyncSession,
        conversation_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AIMessage]:
        """Get message history for a conversation."""
        result = await db.execute(
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation_id)
            .order_by(AIMessage.created_at)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


class AIService:
    """Main AI service aggregating all sub-services."""

    def __init__(self):
        self.conversation_service = ConversationManagementService()
        self.chat_service = ChatProcessingService()
        self.history_service = ConversationHistoryService()

    async def create_conversation(
        self, db: AsyncSession, user_id: int, title: Optional[str] = None
    ) -> AIConversation:
        return await self.conversation_service.create_conversation(db, user_id, title)

    async def get_conversation(
        self, db: AsyncSession, conversation_id: int
    ) -> Optional[AIConversation]:
        return await self.conversation_service.get_conversation(
            db, conversation_id
        )

    async def get_user_conversations(
        self, db: AsyncSession, user_id: int, limit: int = 50
    ) -> List[AIConversation]:
        return await self.conversation_service.get_user_conversations(
            db, user_id, limit
        )

    async def chat(
        self,
        db: AsyncSession,
        user_id: int,
        message: str,
        conversation_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        return await self.chat_service.chat(db, user_id, message, conversation_id)

    async def get_conversation_history(
        self, db: AsyncSession, conversation_id: int, limit: int = 100
    ) -> List[AIMessage]:
        return await self.history_service.get_conversation_history(
            db, conversation_id, limit
        )


ai_service = AIService()