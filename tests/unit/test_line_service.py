"""
Unit tests for LINE service.
"""
import pytest
from unittest.mock import Mock, patch

from app.services.line_service import LINEService
from app.models.line_user import LINEUser
from app.models.user import User

def test_get_or_create_line_user_new(db):
    """Test creating a new LINE user."""
    line_service = LINEService()
    line_user_id = "U1234567890"
    
    # Mock the LINE API response
    with patch('app.services.line_service.LineBotApi') as mock_line_bot_api:
        mock_instance = mock_line_bot_api.return_value
        mock_instance.get_profile.return_value = Mock(
            user_id=line_user_id,
            display_name="Test User",
            picture_url="http://example.com/pic.jpg",
            status_message="Hello"
        )
        
        line_user = line_service.get_or_create_line_user(line_user_id, db)
        
        assert line_user.line_user_id == line_user_id
        assert line_user.display_name == "Test User"
        assert line_user.picture_url == "http://example.com/pic.jpg"
        assert line_user.status_message == "Hello"

def test_get_or_create_line_user_existing(db):
    """Test getting an existing LINE user."""
    line_service = LINEService()
    line_user_id = "U1234567890"
    
    # Create an existing user
    existing_user = LINEUser(
        line_user_id=line_user_id,
        display_name="Existing User",
        picture_url="http://example.com/existing.jpg",
        status_message="Existing"
    )
    db.add(existing_user)
    db.commit()
    
    # Mock the LINE API (should not be called)
    with patch('app.services.line_service.LineBotApi') as mock_line_bot_api:
        mock_instance = mock_line_bot_api.return_value
        line_user = line_service.get_or_create_line_user(line_user_id, db)
        
        # Should return the existing user without calling the API
        assert line_user.line_user_id == line_user_id
        assert line_user.display_name == "Existing User"
        assert line_user.picture_url == "http://example.com/existing.jpg"
        assert line_user.status_message == "Existing"
        mock_instance.get_profile.assert_not_called()

def test_send_text_message_success(db):
    """Test sending a text message successfully."""
    line_service = LINEService()
    line_user_id = "U1234567890"
    message = "Hello, world!"
    
    with patch('app.services.line_service.LineBotApi') as mock_line_bot_api:
        mock_instance = mock_line_bot_api.return_value
        mock_instance.push_message.return_value = None  # Success
        
        result = line_service.send_text_message(line_user_id, message)
        
        assert result is True
        mock_instance.push_message.assert_called_once()
        # Check that the message sent is a TextSendMessage
        args, kwargs = mock_instance.push_message.call_args
        assert args[0] == line_user_id
        # The second argument should be a TextSendMessage instance
        # We can't easily check the type without importing, but we can check the call was made

def test_send_text_message_failure(db):
    """Test sending a text message that fails."""
    line_service = LINEService()
    line_user_id = "U1234567890"
    message = "Hello, world!"
    
    with patch('app.services.line_service.LineBotApi') as mock_line_bot_api:
        mock_instance = mock_line_bot_api.return_value
        mock_instance.push_message.side_effect = Exception("API Error")
        
        result = line_service.send_text_message(line_user_id, message)
        
        assert result is False

def test_get_or_create_db_user_new(db):
    """Test creating a new DB user linked to LINE user."""
    line_service = LINEService()
    line_user_id = "U1234567890"
    
    with patch('app.services.line_service.LineBotApi') as mock_line_bot_api:
        mock_instance = mock_line_bot_api.return_value
        mock_instance.get_profile.return_value = Mock(
            user_id=line_user_id,
            display_name="Test User",
            picture_url="http://example.com/pic.jpg",
            status_message="Hello"
        )
        
        user = line_service.get_or_create_db_user(line_user_id, db)
        
        assert user.email == f"{line_user_id}@line.user"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.full_name == "Test User"
        # Check that the password is set (it's a dummy hash)
        assert user.hashed_password.startswith("$2b$12$")

def test_get_or_create_db_user_existing(db):
    """Test getting an existing DB user."""
    line_service = LINEService()
    line_user_id = "U1234567890"
    email = f"{line_user_id}@line.user"
    
    # Create an existing user
    existing_user = User(
        email=email,
        hashed_password="$2b$12$existinghash",
        is_active=True,
        is_superuser=False,
        full_name="Existing User"
    )
    db.add(existing_user)
    db.commit()
    
    with patch('app.services.line_service.LineBotApi') as mock_line_bot_api:
        mock_instance = mock_line_bot_api.return_value
        # Even if we mock the LINE API, it should not affect the existing user
        user = line_service.get_or_create_db_user(line_user_id, db)
        
        assert user.id == existing_user.id
        assert user.email == email
        assert user.full_name == "Existing User"