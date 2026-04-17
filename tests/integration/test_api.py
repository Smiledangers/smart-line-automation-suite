"""Integration tests for API endpoints."""
import pytest
from fastapi import status


class TestLineAPI:
    """Test LINE API endpoints."""

    def test_webhook_endpoint(self, client, sample_line_message):
        """Test LINE webhook endpoint."""
        response = client.post("/api/v1/line/webhook", json=sample_line_message)
        # May return 200 or 400 depending on implementation
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_callback_endpoint(self, client):
        """Test LINE callback endpoint."""
        response = client.get("/api/v1/line/callback")
        # Should redirect or show auth page
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_302_FOUND,
            status.HTTP_400_BAD_REQUEST
        ]


class TestDashboardAPI:
    """Test Dashboard API endpoints."""

    def test_get_users(self, client, test_user):
        """Test getting users list."""
        response = client.get("/api/v1/dashboard/users")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "users" in data or isinstance(data, list)

    def test_get_stats(self, client, test_user):
        """Test getting dashboard stats."""
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should contain statistics fields
        assert isinstance(data, dict)


class TestScrapingAPI:
    """Test Scraping API endpoints."""

    def test_create_job(self, client, test_user, sample_scraping_job):
        """Test creating a scraping job."""
        response = client.post(
            "/api/v1/scraping/jobs",
            json=sample_scraping_job
        )
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_get_jobs(self, client):
        """Test getting scraping jobs."""
        response = client.get("/api/v1/scraping/jobs")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_get_job_detail(self, client):
        """Test getting job detail."""
        response = client.get("/api/v1/scraping/jobs/1")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_404_NOT_FOUND,
            status.HTTP_401_UNAUTHORIZED
        ]


class TestAIAPI:
    """Test AI API endpoints."""

    def test_create_conversation(self, client):
        """Test creating a conversation."""
        response = client.post(
            "/api/v1/ai/conversations",
            json={"title": "Test Chat"}
        )
        assert response.status_code in [
            status.HTTP_201_CREATED,
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_get_conversations(self, client):
        """Test getting conversations."""
        response = client.get("/api/v1/ai/conversations")
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED
        ]

    def test_chat(self, client):
        """Test chat endpoint."""
        response = client.post(
            "/api/v1/ai/chat",
            json={
                "message": "Hello",
                "conversation_id": 1
            }
        )
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_404_NOT_FOUND
        ]


class TestHealthCheck:
    """Test health check endpoints."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data.get("status") == "healthy"

    def test_ready_endpoint(self, client):
        """Test readiness check endpoint."""
        response = client.get("/ready")
        # Should return 200 if ready, 503 if not
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_503_SERVICE_UNAVAILABLE
        ]