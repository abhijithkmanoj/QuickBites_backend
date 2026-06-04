from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class DeliveryPartnerBase(BaseModel):
    vehicle_type: str = Field(..., min_length=1, max_length=120)
    license_number: str = Field(..., min_length=1, max_length=120)
    aadhar_number: Optional[str] = Field(default=None, max_length=12)
    license_image_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    vehicle_number: Optional[str] = Field(default=None, max_length=20)
    is_available: Optional[bool] = True


class DeliveryPartnerCreate(DeliveryPartnerBase):
    pass


class DeliveryPartnerUpdate(BaseModel):
    vehicle_type: Optional[str] = Field(default=None, min_length=1, max_length=120)
    license_number: Optional[str] = Field(default=None, min_length=1, max_length=120)
    aadhar_number: Optional[str] = Field(default=None, max_length=12)
    license_image_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    vehicle_number: Optional[str] = Field(default=None, max_length=20)
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    is_available: Optional[bool] = None


class DeliveryPartnerRead(BaseModel):
    id: UUID
    user_id: UUID
    vehicle_type: str
    license_number: str
    aadhar_number: Optional[str] = None
    license_image_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    vehicle_number: Optional[str] = None
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    rating: float
    is_available: bool
    verification_status: VerificationStatus
    rejection_reason: Optional[str] = None
    total_deliveries: int
    earnings_today: float
    earnings_total: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VerificationStatusRead(BaseModel):
    status: VerificationStatus
    rejection_reason: Optional[str] = None
