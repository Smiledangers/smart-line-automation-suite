"""Tests for authentication endpoints."""
import pytest
from fastapi import status


class TestAuthRegister:
    """Test user registration."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "TestPass123",
                "full_name": "New User"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert "id" in data

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email fails."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "password": "TestPass123",
            }
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestAuthLogin:
    """Test user login."""

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "password123"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password fails."""
        response = client.post(
            "/api/v1/auth/login",
            data={
                "username": test_user.email,
                "password": "wrongpassword"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthMe:
    """Test get current user."""

    def test_get_me_unauthorized(self, client):
        """Test get me without token fails."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_me_authorized(self, client, auth_headers):
        """Test get me with valid token."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK


class TestAuthLogout:
    """Test user logout."""

    def test_logout(self, client):
        """Test logout endpoint."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == status.HTTP_200_OK