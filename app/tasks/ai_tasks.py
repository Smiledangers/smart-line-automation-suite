"""
Celery tasks for AI processing.
"""
from celery import Celery
from typing import Dict, Any
import logging
from datetime import datetime

from app.core.config import settings
from app.core.database import SessionLocal
from app.Models.ai_conversation import AIConversation
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    'ai_tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

@celery_app.task(bind=True)
def process_ai_message(self, conversation_id: int, message: str, user_id: int) -> Dict[str, Any]:
    """Process an AI message asynchronously."""
    db = SessionLocal()
    try:
        # Get conversation
        conversation = db.query(AIConversation).filter(
            AIConversation.id == conversation_id,
            AIConversation.user_id == user_id
        ).first()
        
        if not conversation:
            return {"status": "error", "message": "Conversation not found or access denied"}
        
        # Import here to avoid circular imports
        import asyncio
        from app.ai.agents.line_agent import line_agent
        
        # Process message
        async def process():
            return await line_agent.process_message(
                message=message,
                conversation_history=conversation.get_message_history(),
                user_context={"user_id": user_id}
            )
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            ai_response = loop.run_until_complete(process())
        finally:
            loop.close()
        
        # Add messages to conversation
        user_msg = {
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        ai_msg = {
            "role": "assistant",
            "content": ai_response["response"],
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": ai_response.get("metadata", {})
        }
        
        # Update conversation
        history = conversation.get_message_history()
        history.extend([user_msg, ai_msg])
        conversation.set_message_history(history)
        conversation.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "status": "success",
            "response": ai_response["response"],
            "conversation_id": conversation_id,
            "metadata": ai_response.get("metadata", {})
        }
    except Exception as e:
        logger.error(f"AI processing task error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@celery_app.task
def generate_ai_summary(conversation_id: int, user_id: int) -> Dict[str, Any]:
    """Generate a summary of a conversation."""
    db = SessionLocal()
    try:
        conversation = db.query(AIConversation).filter(
            AIConversation.id == conversation_id,
            AIConversation.user_id == user_id
        ).first()
        
        if not conversation:
            return {"status": "error", "message": "Conversation not found"}
        
        # Simple summary - in production, this would use a proper summarization model
        history = conversation.get_message_history()
        if not history:
            return {"status": "success", "summary": "Empty conversation"}
        
        # Count messages
        user_messages = [m for m in history if m.get("role") == "user"]
        ai_messages = [m for m in history if m.get("role") == "assistant"]
        
        summary = f"""
對話摘要：
- 總訊息數：{len(history)}
- 使用者訊息：{len(user_messages)}
- AI 回覆：{len(ai_messages)}
- 建立時間：{conversation.created_at}
- 最後更新：{conversation.updated_at}
        """.strip()
        
        return {"status": "success", "summary": summary}
    except Exception as e:
        logger.error(f"AI summary task error: {e}")
        return {"status": "error", "message": str(e)}
    finally:
        db.close()