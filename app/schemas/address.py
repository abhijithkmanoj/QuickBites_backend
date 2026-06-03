from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, constr


class AddressBase(BaseModel):
    street: constr(min_length=1, max_length=255)
    city: constr(min_length=1, max_length=120)
    state: constr(min_length=1, max_length=120)
    postal_code: constr(min_length=1, max_length=20)
    phone: Optional[constr(max_length=20)] = None
    landmark: Optional[constr(max_length=255)] = None
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseModel):
    street: Optional[constr(min_length=1, max_length=255)] = None
    city: Optional[constr(min_length=1, max_length=120)] = None
    state: Optional[constr(min_length=1, max_length=120)] = None
    postal_code: Optional[constr(min_length=1, max_length=20)] = None
    phone: Optional[constr(max_length=20)] = None
    landmark: Optional[constr(max_length=255)] = None
    is_default: Optional[bool] = None


class AddressRead(AddressBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
