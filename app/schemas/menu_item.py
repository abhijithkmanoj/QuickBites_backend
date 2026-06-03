from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, constr


class MenuItemBase(BaseModel):
    restaurant_id: UUID
    category: Optional[constr(max_length=120)] = None
    name: constr(min_length=1, max_length=120)
    description: Optional[str] = None
    price: float = Field(..., ge=0.0)
    image_url: Optional[str] = None
    is_veg: bool = False
    is_available: bool = True


class MenuItemCreate(MenuItemBase):
    pass


class MenuItemUpdate(BaseModel):
    category: Optional[constr(max_length=120)] = None
    name: Optional[constr(min_length=1, max_length=120)] = None
    description: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0.0)
    image_url: Optional[str] = None
    is_veg: Optional[bool] = None
    is_available: Optional[bool] = None


class MenuItemRead(MenuItemBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
