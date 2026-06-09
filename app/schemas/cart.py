from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, constr


class CartItemBase(BaseModel):
    menu_item_id: Optional[UUID] = None
    name: constr(min_length=1, max_length=120)
    price: float = Field(..., ge=0.0)
    quantity: int = Field(default=1, ge=1)


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1)


class CartItemRead(CartItemBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CartRead(BaseModel):
    id: UUID
    user_id: UUID
    restaurant_id: UUID
    items: List[CartItemRead] = []
    applicable_promotions: List[dict] = []
    created_at: datetime

    class Config:
        from_attributes = True


class CartAddItemRequest(BaseModel):
    restaurant_id: UUID
    item: CartItemCreate
