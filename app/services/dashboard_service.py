"""Dashboard service layer for dashboard management."""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.user import User
from app.models.line_user import LINEUser
from app.models.scraping_job import ScrapingJob
from app.models.scraping_result import ScrapingResult
from app.models.ai_conversation import AIConversation
from app.schemas.dashboard import UserCreate, UserUpdate, StatsResponse

logger = logging.getLogger(__name__)

class UserService:
    """Service for user management."""
    
    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Get list of users with pagination."""
        return db.query(User).offset(skip).limit(limit).all()
    
    def create_user(self, db: Session, user_in: dict) -> User:
        """Create a new user."""
        user = User(**user_in)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    def update_user(self, db: Session, user_id: int, user_in: dict) -> Optional[User]:
        """Update user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        
        for field, value in user_in.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user
    
    def delete_user(self, db: Session, user_id: int) -> bool:
        """Delete user."""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        
        db.delete(user)
        db.commit()
        return True

class StatsService:
    """Service for dashboard statistics."""
    
    def get_stats(self, db: Session) -> StatsResponse:
        """Get dashboard statistics."""
        user_count = db.query(User).count()
        line_user_count = db.query(LINEUser).count()
        scraping_job_count = db.query(ScrapingJob).count()
        completed_job_count = db.query(ScrapingJob).filter(ScrapingJob.status == "completed").count()
        ai_conversation_count = db.query(AIConversation).count()
        
        return StatsResponse(
            user_count=user_count,
            line_user_count=line_user_count,
            scraping_job_count=scraping_job_count,
            completed_job_count=completed_job_count,
            ai_conversation_count=ai_conversation_count
        )

class DashboardService:
    """Main dashboard service that aggregates sub-services."""
    
    def __init__(self):
        self.user_service = UserService()
        self.stats_service = StatsService()
    
    # Delegate methods for backward compatibility
    def get_user(self, db: Session, user_id: int) -> Optional[User]:
        return self.user_service.get_user(db, user_id)
    
    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return self.user_service.get_users(db, skip, limit)
    
    def create_user(self, db: Session, user_in: dict) -> User:
        return self.user_service.create_user(db, user_in)
    
    def update_user(self, db: Session, user_id: int, user_in: dict) -> Optional[User]:
        return self.user_service.update_user(db, user_id, user_in)
    
    def delete_user(self, db: Session, user_id: int) -> bool:
        return self.user_service.delete_user(db, user_id)
    
    def get_stats(self, db: Session) -> StatsResponse:
        return self.stats_service.get_stats(db)

dashboard_service = DashboardService()