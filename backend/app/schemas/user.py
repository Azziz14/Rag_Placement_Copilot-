"""Pydantic schemas for User models and Authentication requests/responses.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """Base fields for User."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user in PostgreSQL database."""
    id: str


class UserUpdate(BaseModel):
    """Schema for updating a user's details."""
    full_name: Optional[str] = None


class UserResponse(UserBase):
    """Schema representing user details in responses."""
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SignUpRequest(BaseModel):
    """Request payload for user signup."""
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    """Request payload for user login."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response containing auth token and user info."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class SyncUserRequest(BaseModel):
    """Request payload to trigger synchronization of a Supabase user."""
    access_token: str
