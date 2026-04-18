"""
Webhook model for external notifications.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.Models.base import Base


class Webhook(Base):
    """Webhook for external notifications."""
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # e.g., "Slack notification"
    user_id = Column(Integer, nullable=True)  # Owner user ID
    
    # URL and events
    url = Column(String(500), nullable=False)
    secret = Column(String(64), nullable=True)  # For signature verification
    
    # Events to trigger
    event_message_received = Column(Boolean, default=True)
    event_message_sent = Column(Boolean, default=False)
    event_conversation_started = Column(Boolean, default=False)
    event_conversation_ended = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime, nullable=True)
    last_status_code = Column(Integer, nullable=True)  # Last HTTP response
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Webhook {self.name}>"