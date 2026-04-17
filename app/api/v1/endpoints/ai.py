"""
AI agent endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import logging

from app.core.database import get_db
from app.models.user import User
from app.schemas.ai import ChatRequest, ChatResponse, ConversationResponse, ConversationHistoryResponse
from app.services.ai_service import ai_service
from app.services.line_service import line_service
from app.core.security import get_current_active_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    chat_request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Chat with AI agent.
    """
    try:
        response = await ai_service.chat(db, chat_request, current_user.id)
        
        # Optional: Send LINE notification if user is linked
        # This would require checking if the user has a LINE ID linked
        
        return response
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/conversations", response_model=List[ConversationResponse])
def get_user_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get all conversations for the current user."""
    conversations = ai_service.get_user_conversations(db, current_user.id)
    return [
        ConversationResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=len(conv.get_message_history()) if conv.message_history else 0
        )
        for conv in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=ConversationHistoryResponse)
def get_conversation_history(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get conversation history."""
    conversation = ai_service.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check ownership
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return ConversationHistoryResponse(
        id=conversation.id,
        title=conversation.title,
        message_history=conversation.get_message_history(),
        created_at=conversation.created_at,
        updated_at=conversation.updated_at
    )


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Delete a conversation."""
    conversation = ai_service.get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check ownership
    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted"}

# Optional: Webhook for sending AI responses via LINE
# This would be called by background tasks or other services