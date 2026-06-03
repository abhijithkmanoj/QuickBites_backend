from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CouponBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=50)
    discount_type: str = Field(..., pattern="^(percentage|fixed)$")
    discount_value: float = Field(..., gt=0)
    usage_limit: Optional[int] = Field(None, gt=0)
    expiry_date: Optional[datetime] = None


class CouponCreate(CouponBase):
    pass


class CouponUpdate(BaseModel):
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    discount_type: Optional[str] = Field(None, pattern="^(percentage|fixed)$")
    discount_value: Optional[float] = Field(None, gt=0)
    usage_limit: Optional[int] = Field(None, gt=0)
    expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class CouponRead(CouponBase):
    id: UUID
    used_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
