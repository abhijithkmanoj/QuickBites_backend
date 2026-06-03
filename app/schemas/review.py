from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    review_text: Optional[str] = None


class ReviewCreate(ReviewBase):
    order_id: UUID
    restaurant_id: UUID
    delivery_partner_id: Optional[UUID] = None


class ReviewRead(ReviewBase):
    id: UUID
    order_id: UUID
    restaurant_id: UUID
    delivery_partner_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True
