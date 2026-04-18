"""Integration tests for AI service endpoints."""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from fastapi import status


class TestAIConversationAPI:
    """Test AI conversation API endpoints."""

    def test_create_conversation(self, client, auth_headers):
        """Test creating a new conversation."""
        response = client.post(
            "/api/v1/ai/conversations",
            json={"title": "Test Conversation"},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "id" in data
        assert data["title"] == "Test Conversation"

    def test_get_conversations(self, client, auth_headers):
        """Test getting user conversations."""
        response = client.get(
            "/api/v1/ai/conversations",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    def test_get_conversations_unauthorized(self, client):
        """Test getting conversations without auth."""
        response = client.get("/api/v1/ai/conversations")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_conversation(self, client, auth_headers):
        """Test getting a specific conversation."""
        # First create a conversation
        create_response = client.post(
            "/api/v1/ai/conversations",
            json={"title": "Test Conv"},
            headers=auth_headers,
        )
        conv_id = create_response.json()["id"]

        # Then get it
        response = client.get(
            f"/api/v1/ai/conversations/{conv_id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == conv_id


class TestAIChatAPI:
    """Test AI chat API endpoints."""

    @patch("app.services.ai_service.ChatProcessingService._generate_response")
    def test_chat_without_conversation(self, mock_generate, client, auth_headers):
        """Test sending a chat message without conversation ID."""
        mock_generate.return_value = "Hello! I'm an AI response."

        response = client.post(
            "/api/v1/ai/chat",
            json={"message": "Hello AI"},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "conversation_id" in data

    @patch("app.services.ai_service.ChatProcessingService._generate_response")
    def test_chat_with_conversation(self, mock_generate, client, auth_headers):
        """Test sending a chat message with conversation ID."""
        # Create a conversation first
        create_response = client.post(
            "/api/v1/ai/conversations",
            json={"title": "Chat Conv"},
            headers=auth_headers,
        )
        conv_id = create_response.json()["id"]

        mock_generate.return_value = "Response to your message."

        response = client.post(
            "/api/v1/ai/chat",
            json={"message": "Hello", "conversation_id": conv_id},
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK

    def test_chat_unauthorized(self, client):
        """Test chat without auth."""
        response = client.post(
            "/api/v1/ai/chat",
            json={"message": "Hello"},
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAIMessageAPI:
    """Test AI message API endpoints."""

    @patch("app.services.ai_service.ChatProcessingService._generate_response")
    def test_get_conversation_messages(self, mock_generate, client, auth_headers):
        """Test getting messages from a conversation."""
        mock_generate.return_value = "Test response."

        # Create conversation and send message
        conv_response = client.post(
            "/api/v1/ai/conversations",
            json={"title": "Msg Test"},
            headers=auth_headers,
        )
        conv_id = conv_response.json()["id"]

        client.post(
            "/api/v1/ai/chat",
            json={"message": "Test", "conversation_id": conv_id},
            headers=auth_headers,
        )

        # Get messages
        response = client.get(
            f"/api/v1/ai/conversations/{conv_id}/messages",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


class TestAIHealthCheck:
    """Test AI service health check."""

    def test_health_endpoint(self, client):
        """Test AI health endpoint."""
        response = client.get("/api/v1/ai/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "status" in data or "model" in data