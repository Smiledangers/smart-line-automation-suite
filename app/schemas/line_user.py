"""LINE user schemas."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class LINEUserBase(BaseModel):
    line_user_id: str
    display_name: Optional[str] = None
    picture_url: Optional[str] = None
    status_message: Optional[str] = None


class LINEUserCreate(LINEUserBase):
    user_id: Optional[int] = None


class LINEUserUpdate(BaseModel):
    display_name: Optional[str] = None
    picture_url: Optional[str] = None
    status_message: Optional[str] = None
    is_active: Optional[bool] = None


class LINEUserInDB(LINEUserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LINEUserResponse(LINEUserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LINEUserList(BaseModel):
    users: list[LINEUserResponse]
    total: int