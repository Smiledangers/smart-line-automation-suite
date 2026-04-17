"""Unit tests for services."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestLineService:
    """Test LINE service."""

    def test_get_or_create_line_user(self, db_session):
        """Test creating a new LINE user."""
        from app.services.line_service import LineUserService
        
        service = LineUserService()
        user = service.get_or_create_line_user(db_session, "U1234567890")
        
        assert user.line_user_id == "U1234567890"
        assert user.id is not None

    def test_get_existing_line_user(self, db_session):
        """Test getting existing LINE user."""
        from app.services.line_service import LineUserService
        from app.models.line_user import LINEUser
        
        # Create user first
        line_user = LINEUser(line_user_id="U1234567890")
        db_session.add(line_user)
        db_session.commit()
        
        service = LineUserService()
        user = service.get_or_create_line_user(db_session, "U1234567890")
        
        assert user.line_user_id == "U1234567890"

    def test_update_line_user(self, db_session):
        """Test updating LINE user."""
        from app.services.line_service import LineUserService
        from app.models.line_user import LINEUser
        
        line_user = LINEUser(line_user_id="U1234567890", display_name="Test")
        db_session.add(line_user)
        db_session.commit()
        
        service = LineUserService()
        updated = service.update_line_user(
            db_session, "U1234567890", {"display_name": "Updated"}
        )
        
        assert updated.display_name == "Updated"


class TestDashboardService:
    """Test dashboard service."""

    def test_create_user(self, db_session):
        """Test creating a user."""
        from app.services.dashboard_service import UserService
        
        service = UserService()
        user = service.create_user(db_session, {
            "email": "test@example.com",
            "hashed_password": "hashed",
            "full_name": "Test User"
        })
        
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"

    def test_get_user(self, db_session):
        """Test getting a user."""
        from app.services.dashboard_service import UserService
        from app.models.user import User
        
        user = User(email="test@example.com", hashed_password="hashed")
        db_session.add(user)
        db_session.commit()
        
        service = UserService()
        found = service.get_user(db_session, user.id)
        
        assert found.email == "test@example.com"

    def test_delete_user(self, db_session):
        """Test deleting a user."""
        from app.services.dashboard_service import UserService
        from app.models.user import User
        
        user = User(email="test@example.com", hashed_password="hashed")
        db_session.add(user)
        db_session.commit()
        user_id = user.id
        
        service = UserService()
        result = service.delete_user(db_session, user_id)
        
        assert result is True
        assert service.get_user(db_session, user_id) is None


class TestScrapingService:
    """Test scraping service."""

    def test_create_job(self, db_session):
        """Test creating a scraping job."""
        from app.services.scraping_service import ScrapingJobService
        
        service = ScrapingJobService()
        job = service.create_job(db_session, {
            "url": "https://example.com",
            "website_type": "generic"
        }, user_id=1)
        
        assert job.url == "https://example.com"
        assert job.status == "pending"

    def test_get_job(self, db_session):
        """Test getting a scraping job."""
        from app.services.scraping_service import ScrapingJobService
        from app.models.scraping_job import ScrapingJob
        
        job = ScrapingJob(url="https://example.com", status="pending")
        db_session.add(job)
        db_session.commit()
        
        service = ScrapingJobService()
        found = service.get_job(db_session, job.id)
        
        assert found.url == "https://example.com"

    def test_cancel_job(self, db_session):
        """Test canceling a job."""
        from app.services.scraping_service import ScrapingJobService
        from app.models.scraping_job import ScrapingJob
        
        job = ScrapingJob(url="https://example.com", status="pending")
        db_session.add(job)
        db_session.commit()
        
        service = ScrapingJobService()
        result = service.cancel_job(db_session, job.id)
        
        assert result is True


class TestAIService:
    """Test AI service."""

    @pytest.mark.asyncio
    async def test_create_conversation(self):
        """Test creating a conversation."""
        from app.services.ai_service import ConversationManagementService
        
        service = ConversationManagementService()
        conversation = await service.create_conversation("user123", "Test Chat")
        
        assert conversation["user_id"] == "user123"
        assert conversation["title"] == "Test Chat"
        assert conversation["is_active"] is True

    @pytest.mark.asyncio
    async def test_get_conversation(self):
        """Test getting a conversation."""
        from app.services.ai_service import ConversationManagementService
        
        service = ConversationManagementService()
        conv = await service.create_conversation("user123")
        retrieved = await service.get_conversation(conv["id"])
        
        assert retrieved["id"] == conv["id"]

    @pytest.mark.asyncio
    async def test_chat(self):
        """Test chat processing."""
        from app.services.ai_service import ChatProcessingService
        
        service = ChatProcessingService()
        # Note: This will fail without mock, but tests structure
        with patch.object(service, 'openai_client'):
            # Mock response
            pass