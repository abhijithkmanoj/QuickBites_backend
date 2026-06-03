from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.core.roles import Role


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: str
    phone: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: Role = Role.customer


class UserLogin(BaseModel):
    email: str
    password: str


class UserRead(BaseModel):
    id: UUID
    name: str
    email: str  # Change to plain str to avoid ValidatedEmail issues
    phone: Optional[str] = None
    role: str
    profile_image: Optional[str] = None
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    language_preference: Optional[str] = None
    notification_preference: Optional[Dict[str, Any]] = None
    privacy_settings: Optional[Dict[str, Any]] = None
    theme_preference: Optional[str] = None
    last_active_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """Fields the user can update on their own profile."""
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    phone: Optional[str] = None
    bio: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None


class UserSettingsUpdate(BaseModel):
    """User preferences / settings update payload."""
    notification_preference: Optional[Dict[str, Any]] = None
    privacy_settings: Optional[Dict[str, Any]] = None
    theme_preference: Optional[str] = None
    language_preference: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class DeactivateAccountRequest(BaseModel):
    password: str  # require password confirmation to deactivate


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str


class UserUpdate(BaseModel):
    """Used by admin endpoints — includes is_active toggling."""
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    language_preference: Optional[str] = None
    notification_preference: Optional[Dict[str, Any]] = None
    privacy_settings: Optional[Dict[str, Any]] = None
    theme_preference: Optional[str] = None
    last_active_at: Optional[datetime] = None
