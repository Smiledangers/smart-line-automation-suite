"""
Web Chat Widget Service - embedded customer service widget.
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import json

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/widget", tags=["widget"])

# Active widget connections
active_connections: Dict[str, WebSocket] = {}
widget_sessions: Dict[str, Dict] = {}


class ChatMessage(BaseModel):
    """Chat message from widget."""
    session_id: str
    message: str
    user_info: Optional[Dict] = None


class ChatResponse(BaseModel):
    """Chat response to widget."""
    session_id: str
    message: str
    type: str = "message"
    timestamp: str = None


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()
    active_connections[session_id] = websocket
    
    # Initialize session
    widget_sessions[session_id] = {
        "connected_at": datetime.utcnow().isoformat(),
        "status": "active"
    }
    
    logger.info(f"Widget session connected: {session_id}")
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            msg_type = message_data.get("type", "message")
            
            if msg_type == "message":
                # Process message through AI service
                user_message = message_data.get("message", "")
                user_info = message_data.get("user_info", {})
                
                # Here you would integrate with your AI/LLM service
                # For now, return a simple response
                response = f"Thanks for your message! We'll get back to you soon. (Session: {session_id})"
                
                await websocket.send_json({
                    "type": "message",
                    "message": response,
                    "timestamp": datetime.utcnow().isoformat()
                })
                
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        logger.info(f"Widget session disconnected: {session_id}")
    finally:
        if session_id in active_connections:
            del active_connections[session_id]
        if session_id in widget_sessions:
            del widget_sessions[session_id]


@router.post("/chat")
async def chat_endpoint(message: ChatMessage) -> Dict[str, Any]:
    """REST endpoint for chat (alternative to WebSocket)."""
    session_id = message.session_id
    
    # Check if user is connected via WebSocket
    if session_id in active_connections:
        websocket = active_connections[session_id]
        try:
            await websocket.send_json({
                "type": "message",
                "message": message.message,
                "timestamp": datetime.utcnow().isoformat()
            })
            return {"status": "sent", "via": "websocket"}
        except Exception as e:
            logger.error(f"WebSocket send error: {e}")
    
    # Return mock response (would integrate with AI/LLM)
    return {
        "status": "response",
        "message": f"Thanks for your message! We'll respond shortly.",
        "session_id": session_id
    }


@router.get("/status")
async def widget_status() -> Dict[str, Any]:
    """Get widget status."""
    return {
        "status": "active",
        "sessions": len(active_connections),
        "platforms": ["line", "telegram", "web"]
    }


@router.post("/broadcast")
async def broadcast_message(message: str) -> Dict[str, Any]:
    """Broadcast message to all connected widget sessions."""
    count = 0
    for session_id, websocket in active_connections.items():
        try:
            await websocket.send_json({
                "type": "broadcast",
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })
            count += 1
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
    
    return {"status": "success", "sent_to": count}