from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, constr, field_validator


class AddressBase(BaseModel):
    street: constr(min_length=1, max_length=255)
    city: constr(min_length=1, max_length=120)
    state: constr(min_length=1, max_length=120)
    postal_code: constr(min_length=1, max_length=20)
    phone: Optional[constr(max_length=20)] = None
    landmark: Optional[constr(max_length=255)] = None
    address_line2: Optional[constr(max_length=255)] = None
    unit: Optional[constr(max_length=64)] = None
    is_default: bool = False
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    formatted_address: Optional[str] = None
    place_id: Optional[str] = None


class AddressCreate(AddressBase):
    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def coerce_numeric(cls, v):
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    @field_validator("place_id", mode="before")
    @classmethod
    def coerce_place_id(cls, v):
        if v is None:
            return None
        return str(v)


class AddressUpdate(BaseModel):
    street: Optional[constr(min_length=1, max_length=255)] = None
    city: Optional[constr(min_length=1, max_length=120)] = None
    state: Optional[constr(min_length=1, max_length=120)] = None
    postal_code: Optional[constr(min_length=1, max_length=20)] = None
    phone: Optional[constr(max_length=20)] = None
    landmark: Optional[constr(max_length=255)] = None
    address_line2: Optional[constr(max_length=255)] = None
    unit: Optional[constr(max_length=64)] = None
    is_default: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    formatted_address: Optional[str] = None
    place_id: Optional[str] = None

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def coerce_numeric_update(cls, v):
        if v is None or v == "":
            return None
        try:
            return float(v)
        except (ValueError, TypeError):
            return None

    @field_validator("place_id", mode="before")
    @classmethod
    def coerce_place_id_update(cls, v):
        if v is None:
            return None
        return str(v)


class AddressRead(AddressBase):
    id: UUID
    user_id: UUID
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    formatted_address: Optional[str] = None
    place_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
