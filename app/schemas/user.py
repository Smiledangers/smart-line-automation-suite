"""User schemas for request/response validation."""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


# Base User
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    is_active: Optional[bool] = True


# User create
class UserCreate(UserBase):
    password: str


# User update
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


# User in DB
class UserInDB(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    hashed_password: str
    is_superuser: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# User response
class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_superuser: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# User list
class UserList(BaseModel):
    users: list[UserResponse]
    total: int