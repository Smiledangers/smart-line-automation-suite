"""Pydantic schemas for request/response validation."""
from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserInDB,
    UserResponse,
    UserList,
)
from app.schemas.line_user import (
    LINEUserBase,
    LINEUserCreate,
    LINEUserUpdate,
    LINEUserInDB,
    LINEUserResponse,
    LINEUserList,
)
from app.schemas.scraping import (
    ScrapingJobBase,
    ScrapingJobCreate,
    ScrapingJobUpdate,
    ScrapingJobInDB,
    ScrapingJobResponse,
    ScrapingJobList,
    ScrapingResultBase,
    ScrapingResultCreate,
    ScrapingResultResponse,
    ScrapingResultList,
)
from app.schemas.ai import (
    ConversationBase,
    ConversationCreate,
    ConversationUpdate,
    ConversationInDB,
    ConversationResponse,
    ConversationList,
    MessageBase,
    MessageCreate,
    MessageResponse,
    MessageList,
    ChatRequest,
    ChatResponse,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserResponse",
    "UserList",
    # LINE User
    "LINEUserBase",
    "LINEUserCreate",
    "LINEUserUpdate",
    "LINEUserInDB",
    "LINEUserResponse",
    "LINEUserList",
    # Scraping
    "ScrapingJobBase",
    "ScrapingJobCreate",
    "ScrapingJobUpdate",
    "ScrapingJobInDB",
    "ScrapingJobResponse",
    "ScrapingJobList",
    "ScrapingResultBase",
    "ScrapingResultCreate",
    "ScrapingResultResponse",
    "ScrapingResultList",
    # AI
    "ConversationBase",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationInDB",
    "ConversationResponse",
    "ConversationList",
    "MessageBase",
    "MessageCreate",
    "MessageResponse",
    "MessageList",
    "ChatRequest",
    "ChatResponse",
]