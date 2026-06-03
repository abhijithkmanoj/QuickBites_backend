from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class OrderItemRead(BaseModel):
    id: UUID
    menu_item_id: Optional[UUID] = None
    name: str
    price: float
    quantity: int

    class Config:
        from_attributes = True


class PaymentRead(BaseModel):
    id: UUID
    amount: float
    method: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrderRead(BaseModel):
    id: UUID
    customer_id: UUID
    restaurant_id: UUID
    address_id: Optional[UUID] = None
    delivery_address_text: Optional[str] = None
    delivery_partner_id: Optional[UUID] = None
    assigned_at: Optional[datetime] = None
    picked_up_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    subtotal: float
    delivery_fee: float
    gst: float
    total_amount: float
    status: str
    delivery_lat: Optional[float] = None
    delivery_lng: Optional[float] = None
    partner_lat: Optional[float] = None
    partner_lng: Optional[float] = None
    route_distance_km: Optional[float] = None
    eta_minutes: Optional[float] = None
    items: List[OrderItemRead] = []
    payment: Optional[PaymentRead] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    address_id: Optional[UUID] = None
    delivery_address_text: Optional[str] = None
    payment_method: str = "cod"


class OrderStatusUpdate(BaseModel):
    status: str


class OrderReject(BaseModel):
    reason: Optional[str] = None


class OrderCancelRequest(BaseModel):
    pass
