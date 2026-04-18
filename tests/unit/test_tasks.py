"""Unit tests for Celery tasks."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime


class TestNotificationTasks:
    """Test notification Celery tasks."""

    @patch("app.tasks.notification_tasks.line_service")
    def test_send_line_notification_success(self, mock_line_service):
        """Test sending LINE notification successfully."""
        from app.tasks.notification_tasks import send_line_notification
        
        mock_line_service.send_text_message.return_value = True
        
        result = send_line_notification("U1234567890", "Test message")
        
        assert result["status"] == "success"
        mock_line_service.send_text_message.assert_called_once()

    @patch("app.tasks.notification_tasks.line_service")
    def test_send_line_notification_failure(self, mock_line_service):
        """Test sending LINE notification failure."""
        from app.tasks.notification_tasks import send_line_notification
        
        mock_line_service.send_text_message.return_value = False
        
        result = send_line_notification("U1234567890", "Test message")
        
        assert result["status"] == "error"

    @patch("app.tasks.notification_tasks.send_email")
    def test_send_email_notification(self, mock_send_email):
        """Test sending email notification."""
        from app.tasks.notification_tasks import send_email_notification
        
        mock_send_email.return_value = {"status": "success"}
        
        result = send_email_notification("test@example.com", "Subject", "Body")
        
        assert result["status"] == "success"


class TestScrapingTasks:
    """Test scraping Celery tasks."""

    @patch("app.tasks.scraping_tasks.scraping_service")
    def test_run_scraping_job(self, mock_scraping_service):
        """Test running scraping job task."""
        from app.tasks.scraping_tasks import run_scraping_job
        
        mock_job = MagicMock()
        mock_job.id = 1
        mock_job.url = "https://example.com"
        mock_scraping_service.get_job.return_value = mock_job
        
        run_scraping_job(1)
        
        mock_scraping_service.get_job.assert_called_once()

    @patch("app.tasks.scraping_tasks.cleanup_old_jobs")
    def test_cleanup_old_scraping_jobs(self, mock_cleanup):
        """Test cleanup old jobs task."""
        from app.tasks.scraping_tasks import cleanup_old_scraping_jobs
        
        mock_cleanup.return_value = {"deleted": 5}
        
        result = cleanup_old_scraping_jobs()
        
        assert result["deleted"] == 5


class TestAITasks:
    """Test AI Celery tasks."""

    @patch("app.tasks.ai_tasks.ai_service")
    def test_process_line_message(self, mock_ai_service):
        """Test processing LINE message with AI."""
        from app.tasks.ai_tasks import process_line_message
        
        mock_ai_service.chat.return_value = {"message": "AI response"}
        
        result = process_line_message("U1234567890", "Hello")
        
        assert result["message"] == "AI response"

    @patch("app.tasks.ai_tasks.ai_service")
    def test_generate_ai_response(self, mock_ai_service):
        """Test generating AI response task."""
        from app.tasks.ai_tasks import generate_ai_response
        
        mock_ai_service.chat.return_value = {"message": "Response"}
        
        result = generate_ai_response(1, "Question?")
        
        assert "message" in result


class TestCeleryApp:
    """Test Celery app configuration."""

    def test_celery_app_configuration(self):
        """Test Celery app is properly configured."""
        from app.tasks.celery_app import celery_app
        
        assert celery_app is not None
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"

    def test_beat_schedule_exists(self):
        """Test beat schedule is configured."""
        from app.tasks.celery_app import celery_app
        
        schedule = celery_app.conf.beat_schedule
        assert schedule is not None
        assert isinstance(schedule, dict)


class TestTaskHelpers:
    """Test task helper functions."""

    @patch("app.tasks.celery_app._call_line_api")
    def test_call_line_api_helper(self, mock_call):
        """Test LINE API helper function."""
        from app.tasks.celery_app import DemoBotTasks
        
        mock_call.return_value = "Processed message"
        
        tasks = DemoBotTasks()
        result = tasks._call_line_api("U123", "Hello")
        
        assert result == "Processed message"

    @patch("app.tasks.celery_app._call_scraper")
    def test_call_scraper_helper(self, mock_call):
        """Test scraper helper function."""
        from app.tasks.celery_app import DemoBotTasks
        
        mock_call.return_value = {"job_id": 1, "data": []}
        
        tasks = DemoBotTasks()
        result = tasks._call_scraper(1, "https://example.com")
        
        assert result["job_id"] == 1

    @patch("app.tasks.celery_app._call_ai")
    def test_call_ai_helper(self, mock_call):
        """Test AI helper function."""
        from app.tasks.celery_app import DemoBotTasks
        
        mock_call.return_value = "AI response"
        
        tasks = DemoBotTasks()
        result = tasks._call_ai(1, "Hello", 0)
        
        assert result == "AI response"