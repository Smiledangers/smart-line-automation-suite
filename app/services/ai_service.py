"""
AI service layer for LangGraph integration.
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import logging

from app.models.ai_conversation import AIConversation
from app.schemas.ai import ChatRequest, ChatResponse, ConversationResponse
from app.ai.agents.line_agent import line_agent
from app.ai.graphs.conversation_graph import conversation_graph

logger = logging.getLogger(__name__)

class AIService:
    def create_conversation(self, db: Session, user_id: int, title: str = None) -> AIConversation:
        """Create a new AI conversation."""
        if not title:
            title = f"對話 {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        
        db_conversation = AIConversation(
            user_id=user_id,
            title=title,
            message_history=[]
        )
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        return db_conversation

    def get_conversation(self, db: Session, conversation_id: int) -> Optional[AIConversation]:
        """Get a specific conversation by ID."""
        return db.query(AIConversation).filter(AIConversation.id == conversation_id).first()

    def get_user_conversations(self, db: Session, user_id: int, limit: int = 50) -> List[AIConversation]:
        """Get conversations for a user."""
        return db.query(AIConversation)\
                .filter(AIConversation.user_id == user_id)\
                .order_by(AIConversation.updated_at.desc())\
                .limit(limit)\
                .all()

    async def chat(self, db: Session, chat_request: ChatRequest, user_id: int) -> ChatResponse:
        """Process a chat message using AI agent."""
        # Get or create conversation
        conversation = None
        if chat_request.conversation_id:
            conversation = self.get_conversation(db, chat_request.conversation_id)
            if not conversation or conversation.user_id != user_id:
                raise ValueError("Conversation not found or access denied")
        else:
            conversation = self.create_conversation(db, user_id)
        
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
            
            db.commit()
            db.refresh(conversation)
            
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
            
            db.commit()
            db.refresh(conversation)
            
            return ChatResponse(
                response=error_message,
                conversation_id=conversation.id,
                message_id=len(conversation.message_history) - 1
            )

    def get_conversation_history(self, db: Session, conversation_id: int) -> List[Dict]:
        """Get conversation history."""
        conversation = self.get_conversation(db, conversation_id)
        if not conversation:
            return []
        return conversation.message_history or []

ai_service = AIService()