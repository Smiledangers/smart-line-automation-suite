"""
Unit tests for dashboard service.
"""
from passlib.context import CryptContext

from app.services.dashboard_service import DashboardService
from app.models.user import User
from app.schemas.dashboard import UserCreate, UserUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def test_get_users(db):
    """Test retrieving users with pagination."""
    dashboard_service = DashboardService()
    
    # Create some test users
    for i in range(15):
        user_in = UserCreate(
            email=f"user{i}@example.com",
            password=f"password{i}",
            full_name=f"User {i}",
            is_active=True,
            is_superuser=(i == 0)  # First user is superuser
        )
        dashboard_service.create_user(db, user_in)
    
    # Get first page
    users = dashboard_service.get_users(db, skip=0, limit=10)
    assert len(users) == 10
    assert users[0].email == "user0@example.com"
    assert users[0].is_superuser is True
    
    # Get second page
    users = dashboard_service.get_users(db, skip=10, limit=10)
    assert len(users) == 5
    assert users[0].email == "user10@example.com"

def test_get_user(db):
    """Test getting a specific user."""
    dashboard_service = DashboardService()
    
    user_in = UserCreate(
        email="test@example.com",
        password="testpass",
        full_name="Test User",
        is_active=True,
        is_superuser=False
    )
    created_user = dashboard_service.create_user(db, user_in)
    
    retrieved_user = dashboard_service.get_user(db, created_user.id)
    assert retrieved_user is not None
    assert retrieved_user.email == "test@example.com"
    assert retrieved_user.full_name == "Test User"
    
    # Test non-existent user
    non_existent = dashboard_service.get_user(db, 99999)
    assert non_existent is None

def test_get_user_by_email(db):
    """Test getting user by email."""
    dashboard_service = DashboardService()
    
    user_in = UserCreate(
        email="test@example.com",
        password="testpass",
        full_name="Test User",
        is_active=True,
        is_superuser=False
    )
    dashboard_service.create_user(db, user_in)
    
    user = dashboard_service.get_user_by_email(db, "test@example.com")
    assert user is not None
    assert user.email == "test@example.com"
    
    # Test non-existent email
    non_existent = dashboard_service.get_user_by_email(db, "nonexistent@example.com")
    assert non_existent is None

def test_create_user(db):
    """Test creating a new user."""
    dashboard_service = DashboardService()
    
    user_in = UserCreate(
        email="newuser@example.com",
        password="newpass",
        full_name="New User",
        is_active=True,
        is_superuser=False
    )
    created_user = dashboard_service.create_user(db, user_in)
    
    assert created_user.id is not None
    assert created_user.email == "newuser@example.com"
    assert created_user.full_name == "New User"
    assert created_user.is_active is True
    assert created_user.is_superuser is False
    # Check that the password is hashed
    assert created_user.hashed_password != "newpass"
    assert pwd_context.verify("newpass", created_user.hashed_password)

def test_update_user(db):
    """Test updating a user."""
    dashboard_service = DashboardService()
    
    user_in = UserCreate(
        email="update@example.com",
        password="oldpass",
        full_name="Old Name",
        is_active=True,
        is_superuser=False
    )
    created_user = dashboard_service.create_user(db, user_in)
    
    # Update the user
    update_in = UserUpdate(
        email="updated@example.com",
        full_name="New Name",
        is_active=False
    )
    updated_user = dashboard_service.update_user(db, created_user.id, update_in)
    
    assert updated_user is not None
    assert updated_user.email == "updated@example.com"
    assert updated_user.full_name == "New Name"
    assert updated_user.is_active is False
    assert updated_user.is_superuser is False  # Should remain unchanged
    
    # Test updating password
    update_in2 = UserUpdate(password="newpass")
    updated_user2 = dashboard_service.update_user(db, created_user.id, update_in2)
    assert updated_user2 is not None
    assert pwd_context.verify("newpass", updated_user2.hashed_password)
    
    # Test non-existent user
    non_existent = dashboard_service.update_user(db, 99999, UserUpdate(email="test@example.com"))
    assert non_existent is None

def test_delete_user(db):
    """Test deleting a user."""
    dashboard_service = DashboardService()
    
    user_in = UserCreate(
        email="delete@example.com",
        password="delpass",
        full_name="Delete User",
        is_active=True,
        is_superuser=False
    )
    created_user = dashboard_service.create_user(db, user_in)
    
    deleted_user = dashboard_service.delete_user(db, created_user.id)
    assert deleted_user is not None
    assert deleted_user.id == created_user.id
    assert deleted_user.email == "delete@example.com"
    
    # Try to delete again
    deleted_again = dashboard_service.delete_user(db, created_user.id)
    assert deleted_again is None
    
    # Try to delete non-existent user
    non_existent = dashboard_service.delete_user(db, 99999)
    assert non_existent is None

def test_get_stats(db):
    """Test getting dashboard statistics."""
    dashboard_service = DashboardService()
    
    # Create test users
    for i in range(5):
        user_in = UserCreate(
            email=f"stats{i}@example.com",
            password=f"pass{i}",
            full_name=f"Stats User {i}",
            is_active=(i % 2 == 0),  # Alternate active/inactive
            is_superuser=(i == 0)   # Only first user is superuser
        )
        dashboard_service.create_user(db, user_in)
    
    stats = dashboard_service.get_stats(db)
    assert stats["total_users"] == 5
    assert stats["active_users"] == 3  # indices 0, 2, 4
    assert stats["superusers"] == 1    # index 0
    assert stats["inactive_users"] == 2  # indices 1, 3