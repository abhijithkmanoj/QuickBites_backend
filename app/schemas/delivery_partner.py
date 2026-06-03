from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DeliveryPartnerBase(BaseModel):
    vehicle_type: str = Field(..., min_length=1, max_length=120)
    license_number: str = Field(..., min_length=1, max_length=120)
    is_available: Optional[bool] = True


class DeliveryPartnerCreate(DeliveryPartnerBase):
    pass


class DeliveryPartnerUpdate(BaseModel):
    vehicle_type: Optional[str] = Field(default=None, min_length=1, max_length=120)
    license_number: Optional[str] = Field(default=None, min_length=1, max_length=120)
    is_available: Optional[bool] = None


class DeliveryPartnerRead(BaseModel):
    id: UUID
    user_id: UUID
    vehicle_type: str
    license_number: str
    rating: float
    is_available: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
