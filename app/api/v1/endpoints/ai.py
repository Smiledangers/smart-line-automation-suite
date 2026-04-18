"""
AI service endpoints with async support and comprehensive features.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.Models.user import User
from app.schemas.ai import ChatRequest, ChatResponse, ConversationResponse, ConversationHistoryResponse
from app.services.ai_service import ai_service
from app.services.line_service import line_service
from app.core.security import get_current_active_user

logger = logging.getLogger(__name__)
router = APIRouter()


# Additional request/response models
class CreateConversationRequest(BaseModel):
    """Request model for creating a new conversation."""
    title: Optional[str] = None


class CreateConversationResponse(BaseModel):
    """Response model for new conversation."""
    id: int
    title: str
    created_at: Optional[str] = None


class MessageResponse(BaseModel):
    """Single message response model."""
    id: int
    role: str
    content: str
    created_at: Optional[str] = None


class ChatRequestInternal(BaseModel):
    """Internal chat request model."""
    message: str
    conversation_id: Optional[int] = None


@router.post("/conversations", response_model=CreateConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: CreateConversationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CreateConversationResponse:
    """
    Create a new AI conversation.
    """
    try:
        conversation = await ai_service.create_conversation(
            db, current_user.id, request.title
        )
        
        return CreateConversationResponse(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at.isoformat() if conversation.created_at else None,
        )
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[ConversationResponse]:
    """
    Get all conversations for the current user.
    """
    try:
        conversations = await ai_service.get_user_conversations(
            db, current_user.id, limit=limit, offset=skip
        )
        
        return [
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                created_at=conv.created_at.isoformat() if conv.created_at else None,
                updated_at=conv.updated_at.isoformat() if conv.updated_at else None,
                message_count=0,  # Would need separate query
            )
            for conv in conversations
        ]
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}", response_model=ConversationHistoryResponse)
async def get_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ConversationHistoryResponse:
    """
    Get a specific conversation with message history.
    """
    try:
        conversation = await ai_service.get_conversation(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404, detail="Conversation not found"
            )
        
        # Check ownership
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Access denied"
            )
        
        # Get message history
        messages = await ai_service.get_conversation_history(db, conversation_id)
        
        return ConversationHistoryResponse(
            id=conversation.id,
            title=conversation.title,
            message_history=[
                {"role": m.role, "content": m.content, "created_at": m.created_at.isoformat() if m.created_at else None}
                for m in messages
            ],
            created_at=conversation.created_at.isoformat() if conversation.created_at else None,
            updated_at=conversation.updated_at.isoformat() if conversation.updated_at else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Delete a conversation.
    """
    try:
        conversation = await ai_service.get_conversation(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404, detail="Conversation not found"
            )
        
        # Check ownership
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=403, detail="Access denied"
            )
        
        # Soft delete
        success = await ai_service.conversation_service.delete_conversation(
            db, conversation_id
        )
        
        if not success:
            raise HTTPException(
                status_code=500, detail="Failed to delete conversation"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ChatResponse:
    """
    Send a message to AI and get a response.
    """
    try:
        # Convert schema to internal format
        request_internal = ChatRequestInternal(
            message=chat_request.message,
            conversation_id=chat_request.conversation_id,
        )
        
        result = await ai_service.chat(
            db,
            user_id=current_user.id,
            message=request_internal.message,
            conversation_id=request_internal.conversation_id,
        )
        
        return ChatResponse(
            message=result["message"],
            conversation_id=result["conversation_id"],
            message_id=result.get("message_id"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Legacy endpoint compatibility
@router.post("/chat/legacy", response_model=ChatResponse)
async def chat_legacy(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ChatResponse:
    """
    Legacy chat endpoint for backward compatibility.
    """
    return await chat(chat_request, db, current_user)


@router.get("/health")
async def ai_health_check() -> dict:
    """
    AI service health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "ai",
        "model": "gpt-4",
    }


@router.post("/conversations/{conversation_id}/restore")
async def restore_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
) -> dict:
    """
    Restore a deleted conversation (admin only).
    """
    try:
        conversation = await ai_service.get_conversation(db, conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=404, detail="Conversation not found"
            )
        
        # Restore (set is_active back to True)
        await ai_service.conversation_service.update_conversation(
            db, conversation_id, {"is_active": True}
        )
        
        return {"status": "success", "message": "Conversation restored"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Need to import this for the dependency
from app.core.security import get_current_active_superuser