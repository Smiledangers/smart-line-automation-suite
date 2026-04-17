"""
AI service layer for LangGraph integration with async support.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging

from app.models.ai_conversation import AIConversation
from app.schemas.ai import ChatRequest, ChatResponse, ConversationResponse
from app.ai.agents.line_agent import line_agent
from app.ai.graphs.conversation_graph import conversation_graph

logger = logging.getLogger(__name__)

class ConversationManagementService:
    """Service for AI conversation management."""
    
    async def create_conversation(self, db: AsyncSession, user_id: int, title: str = None) -> AIConversation:
        """Create a new AI conversation."""
        if not title:
            title = f"對話 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        
        db_conversation = AIConversation(
            user_id=user_id,
            title=title,
            message_history=[]
        )
        db.add(db_conversation)
        await db.commit()
        await db.refresh(db_conversation)
        return db_conversation

    async def get_conversation(self, db: AsyncSession, conversation_id: int) -> Optional[AIConversation]:
        """Get a specific conversation by ID."""
        result = await db.execute(select(AIConversation).filter(AIConversation.id == conversation_id))
        return result.scalar_one_or_none()

    async def get_user_conversations(self, db: AsyncSession, user_id: int, limit: int = 50) -> List[AIConversation]:
        """Get conversations for a user."""
        result = await db.execute(
            select(AIConversation)
            .filter(AIConversation.user_id == user_id)
            .order_by(AIConversation.updated_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

class ChatProcessingService:
    """Service for processing AI chat messages."""
    
    async def chat(self, db: AsyncSession, chat_request: ChatRequest, user_id: int) -> ChatResponse:
        """Process a chat message using AI agent."""
        # Get or create conversation
        conversation = None
        if chat_request.conversation_id:
            conversation = await self.get_conversation(db, chat_request.conversation_id)
            if not conversation or conversation.user_id != user_id:
                raise ValueError("Conversation not found or access denied")
        else:
            conversation = await ConversationManagementService().create_conversation(db, user_id)
        
        # Add user message to history
        user_message = {
            "role": "user",
            "content": chat_request.message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Process with AI agent
        try:
            ai_response = await line_agent.process_message(
                message=chat_request.message,
                conversation_history=conversation.message_history or [],
                user_context={"user_id": user_id}
            )
            
            # Add AI response to history
            ai_message = {
                "role": "assistant",
                "content": ai_response["response"],
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": ai_response.get("metadata", {})
            }
            
            # Update conversation
            conversation.message_history = (conversation.message_history or []) + [user_message, ai_message]
            conversation.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(conversation)
            
            return ChatResponse(
                response=ai_response["response"],
                conversation_id=conversation.id,
                message_id=len(conversation.message_history) - 1,
                metadata=ai_response.get("metadata", {})
            )
        except Exception as e:
            logger.error(f"AI processing error: {e}")
            # Return error message
            error_message = "抱歉，我在處理您的訊息時遇到了一些問題。請稍後再試。"
            
            ai_message = {
                "role": "assistant",
                "content": error_message,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            conversation.message_history = (conversation.message_history or []) + [user_message, ai_message]
            conversation.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(conversation)
            
            return ChatResponse(
                response=error_message,
                conversation_id=conversation.id,
                message_id=len(conversation.message_history) - 1
            )

    async def get_conversation(self, db: AsyncSession, conversation_id: int) -> Optional[AIConversation]:
        """Get a specific conversation by ID."""
        result = await db.execute(select(AIConversation).filter(AIConversation.id == conversation_id))
        return result.scalar_one_or_none()

class ConversationHistoryService:
    """Service for getting conversation history."""
    
    def get_conversation_history(self, conversation: AIConversation) -> List[Dict]:
        """Get conversation history."""
        if not conversation:
            return []
        return conversation.message_history or []

# Main AI service that aggregates sub-services (for backward compatibility)
class AIService:
    def __init__(self):
        self.conversation_service = ConversationManagementService()
        self.chat_service = ChatProcessingService()
        self.history_service = ConversationHistoryService()
    
    # Delegate methods for backward compatibility
    async def create_conversation(self, db: AsyncSession, user_id: int, title: str = None) -> AIConversation:
        return await self.conversation_service.create_conversation(db, user_id, title)
    
    async def get_conversation(self, db: AsyncSession, conversation_id: int) -> Optional[AIConversation]:
        return await self.conversation_service.get_conversation(db, conversation_id)
    
    async def get_user_conversations(self, db: AsyncSession, user_id: int, limit: int = 50) -> List[AIConversation]:
        return await self.conversation_service.get_user_conversations(db, user_id, limit)
    
    async def chat(self, db: AsyncSession, chat_request: ChatRequest, user_id: int) -> ChatResponse:
        return await self.chat_service.chat(db, chat_request, user_id)
    
    def get_conversation_history(self, conversation: AIConversation) -> List[Dict]:
        return self.history_service.get_conversation_history(conversation)

ai_service = AIService()