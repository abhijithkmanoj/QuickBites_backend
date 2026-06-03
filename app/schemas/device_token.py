from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class DeviceTokenCreate(BaseModel):
    token: str
    platform: Optional[str] = None


class DeviceTokenRead(BaseModel):
    id: UUID
    user_id: UUID
    token: str
    platform: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
