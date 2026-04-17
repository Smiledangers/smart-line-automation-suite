"""LINE User model."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.Models.base import Base


class LINEUser(Base):
    """LINE user model."""

    __tablename__ = "line_users"

    id = Column(Integer, primary_key=True, index=True)
    line_user_id = Column(String(255), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    display_name = Column(String(255), nullable=True)
    picture_url = Column(String(512), nullable=True)
    status_message = Column(String(512), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="line_users")