"""Pytest fixtures for testing."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db


# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create test database session."""
    from app.models.base import Base
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create test client."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Create test user."""
    from app.models.user import User
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client):
    """Get authentication headers."""
    # This would require actual JWT token generation
    return {"Authorization": "Bearer test-token"}


@pytest.fixture
def sample_line_message():
    """Sample LINE webhook message."""
    return {
        "destination": "U1234567890abcdef",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "1234567890",
                    "text": "Hello"
                },
                "webhookEventId": "test_event_id",
                "timestamp": 1234567890000,
                "replyToken": "test_reply_token",
                "source": {
                    "type": "user",
                    "userId": "U1234567890abcdef"
                }
            }
        ]
    }


@pytest.fixture
def sample_scraping_job():
    """Sample scraping job data."""
    return {
        "url": "https://example.com",
        "website_type": "generic",
        "priority": 1,
        "max_retries": 3
    }


@pytest.fixture
def sample_ai_message():
    """Sample AI chat message."""
    return {
        "message": "Hello, how are you?",
        "conversation_id": 1
    }