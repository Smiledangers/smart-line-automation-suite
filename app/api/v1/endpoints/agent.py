"""
Customer Service endpoints for AI ↔ Human handoff.
"""
import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.core.database import get_db
from app.schemas.ai import ConversationResponse, ConversationList
from app.Models.ai_conversation import AIConversation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/agent", tags=["agent"])


@router.get("/conversations", response_model=ConversationList)
async def list_agent_conversations(
    status: Optional[str] = Query(None, description="Filter by status: pending, active, closed"),
    platform: Optional[str] = Query(None, description="Filter by platform"),
    assigned_to: Optional[int] = Query(None, description="Filter by assigned agent"),
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List conversations for agent dashboard."""
    query = select(AIConversation)
    
    if status:
        query = query.where(AIConversation.status == status)
    if platform:
        query = query.where(AIConversation.platform == platform)
    if assigned_to:
        query = query.where(AIConversation.assigned_agent_id == assigned_to)
    
    # For agents, show conversations assigned to them or pending
    if assigned_to:
        query = query.where(
            or_(
                AIConversation.assigned_agent_id == assigned_to,
                AIConversation.status == "pending"
            )
        )
    
    query = query.offset(skip).limit(limit).order_by(AIConversation.updated_at.desc())
    
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    # Get total count
    count_query = select(AIConversation)
    if status:
        count_query = count_query.where(AIConversation.status == status)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())
    
    return {"conversations": list(conversations), "total": total}


@router.get("/conversations/pending", response_model=ConversationList)
async def list_pending_conversations(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List pending conversations waiting for agent."""
    query = (
        select(AIConversation)
        .where(AIConversation.status == "pending")
        .offset(skip)
        .limit(limit)
        .order_by(AIConversation.created_at.asc())
    )
    
    result = await db.execute(query)
    conversations = result.scalars().all()
    
    count_result = await db.execute(
        select(AIConversation).where(AIConversation.status == "pending")
    )
    total = len(count_result.scalars().all())
    
    return {"conversations": list(conversations), "total": total}


@router.post("/conversations/{conversation_id}/assign")
async def assign_conversation(
    conversation_id: int,
    agent_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Assign a conversation to an agent."""
    result = await db.execute(
        select(AIConversation).where(AIConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation.assigned_agent_id = agent_id
    conversation.status = "active"
    conversation.agent_type = "human"
    conversation.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(conversation)
    
    logger.info(f"Conversation {conversation_id} assigned to agent {agent_id}")
    return {"status": "success", "message": f"Assigned to agent {agent_id}"}


@router.post("/conversations/{conversation_id}/handoff")
async def handoff_conversation(
    conversation_id: int,
    target: str = "ai",  # "ai" or "human"
    db: AsyncSession = Depends(get_db),
):
    """
    Handoff conversation between AI and Human agent.
    
    - target="ai": Transfer from human agent back to AI
    - target="human": Transfer from AI to human agent
    """
    result = await db.execute(
        select(AIConversation).where(AIConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if target == "ai":
        # Transfer to AI
        conversation.agent_type = "ai"
        conversation.status = "active"
        conversation.assigned_agent_id = None
        message = "Conversation transferred to AI"
    elif target == "human":
        # Transfer to human agent
        conversation.agent_type = "human"
        conversation.status = "pending"  # Waiting for agent to pick up
        message = "Conversation marked for human agent"
    else:
        raise HTTPException(status_code=400, detail="Invalid target: must be 'ai' or 'human'")
    
    conversation.updated_at = datetime.utcnow()
    await db.commit()
    
    logger.info(f"Conversation {conversation_id} handoff to {target}")
    return {"status": "success", "message": message}


@router.post("/conversations/{conversation_id}/close")
async def close_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Close a conversation."""
    result = await db.execute(
        select(AIConversation).where(AIConversation.id == conversation_id)
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation.status = "closed"
    conversation.is_active = False
    conversation.updated_at = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"Conversation {conversation_id} closed")
    return {"status": "success", "message": "Conversation closed"}


@router.get("/stats")
async def get_agent_stats(
    db: AsyncSession = Depends(get_db),
):
    """Get agent dashboard statistics."""
    # Pending count
    pending_result = await db.execute(
        select(AIConversation).where(AIConversation.status == "pending")
    )
    pending_count = len(pending_result.scalars().all())
    
    # Active human conversations
    active_result = await db.execute(
        select(AIConversation).where(
            AIConversation.agent_type == "human",
            AIConversation.status == "active"
        )
    )
    active_count = len(active_result.scalars().all())
    
    # Total conversations today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(AIConversation).where(AIConversation.created_at >= today)
    )
    today_count = len(today_result.scalars().all())
    
    return {
        "pending": pending_count,
        "active_human": active_count,
        "created_today": today_count,
    }