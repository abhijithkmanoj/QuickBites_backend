from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class UserFavoriteRead(BaseModel):
    id: UUID
    user_id: UUID
    # Matches the model fields 'favorite_id' and 'favorite_type'
    favorite_id: UUID
    favorite_type: str
    # 'entity_name' does not exist on the model; if you need it, 
    # it must be populated by the service layer or removed.
    entity_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
