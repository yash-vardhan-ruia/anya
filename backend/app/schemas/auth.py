"""
CareVoice AI Hospital Platform - Auth Schemas.

Pydantic models for admin authentication and registration.
"""

from datetime import datetime
import uuid
from pydantic import BaseModel, EmailStr, Field
from app.core.constants import AdminRole


class LoginRequest(BaseModel):
    """Request payload for admin login."""
    username: EmailStr = Field(..., description="Admin login email address")
    password: str = Field(..., description="Plaintext password")


class TokenResponse(BaseModel):
    """Response containing JWT access token."""
    access_token: str
    token_type: str = "bearer"
    role: AdminRole
    full_name: str


class AdminCreate(BaseModel):
    """Schema for creating a new admin user."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    full_name: str = Field(..., min_length=2, max_length=255)
    role: AdminRole = AdminRole.ADMIN


class AdminResponse(BaseModel):
    """Response schema for admin user details."""
    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: AdminRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AdminUpdate(BaseModel):
    """Schema to update the current user profile."""
    email: EmailStr | None = None
    full_name: str | None = Field(None, min_length=2, max_length=255)


class PasswordUpdate(BaseModel):
    """Schema to change current user's password."""
    current_password: str = Field(..., description="The current plaintext password")
    new_password: str = Field(..., min_length=8, description="The new plaintext password, min 8 chars")
