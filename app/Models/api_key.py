"""
API Key model for third-party access.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from app.Models.base import Base


class APIKey(Base):
    """API Key for external access."""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)  # e.g., "Company A"
    user_id = Column(Integer, nullable=True)  # Owner user ID
    
    # Permissions
    can_send_message = Column(Boolean, default=True)
    can_read_conversation = Column(Boolean, default=True)
    can_read_stats = Column(Boolean, default=False)
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60)
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<APIKey {self.name}>"