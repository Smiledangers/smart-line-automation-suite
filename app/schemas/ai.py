"""AI conversation schemas."""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ConversationBase(BaseModel):
    title: Optional[str] = None
    model: Optional[str] = "gpt-4"


class ConversationCreate(ConversationBase):
    user_id: Optional[int] = None


class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_active: Optional[bool] = None


class ConversationInDB(ConversationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ConversationResponse(ConversationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ConversationList(BaseModel):
    conversations: list[ConversationResponse]
    total: int


class MessageBase(BaseModel):
    role: str
    content: str


class MessageCreate(MessageBase):
    conversation_id: int


class MessageResponse(MessageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None


class MessageList(BaseModel):
    messages: list[MessageResponse]
    total: int


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: int
    message_id: Optional[str] = None