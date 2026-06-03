from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserActivityRead(BaseModel):
    id: str
    user_id: str
    activity_type: str
    description: Optional[str]
    entity_id: Optional[str]
    entity_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
