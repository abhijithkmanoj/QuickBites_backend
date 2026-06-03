from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PaymentRead(BaseModel):
    id: UUID
    order_id: UUID
    user_id: UUID
    amount: float
    method: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
