from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserFavoriteRead(BaseModel):
    id: str
    user_id: str
    entity_id: str
    entity_type: str
    entity_name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
