from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class RestaurantOwnerProfileBase(BaseModel):
    business_name: str = Field(..., min_length=1, max_length=255)
    gstin: Optional[str] = Field(default=None, max_length=15)
    fssai_license_number: Optional[str] = Field(default=None, max_length=14)
    bank_account_number: Optional[str] = Field(default=None, max_length=50)
    ifsc_code: Optional[str] = Field(default=None, max_length=11)


class RestaurantOwnerProfileCreate(RestaurantOwnerProfileBase):
    pass


class RestaurantOwnerProfileUpdate(BaseModel):
    business_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    gstin: Optional[str] = Field(default=None, max_length=15)
    fssai_license_number: Optional[str] = Field(default=None, max_length=14)
    bank_account_number: Optional[str] = Field(default=None, max_length=50)
    ifsc_code: Optional[str] = Field(default=None, max_length=11)


class RestaurantOwnerProfileRead(BaseModel):
    id: UUID
    user_id: UUID
    business_name: str
    gstin: Optional[str] = None
    fssai_license_number: Optional[str] = None
    bank_account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    verification_status: VerificationStatus
    rejection_reason: Optional[str] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VerificationStatusRead(BaseModel):
    status: VerificationStatus
    rejection_reason: Optional[str] = None