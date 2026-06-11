from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, constr


class RestaurantBase(BaseModel):
    name: constr(min_length=1, max_length=120)
    description: Optional[str] = None
    cuisine: Optional[constr(max_length=120)] = None
    address: constr(min_length=1, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rating: Optional[float] = Field(default=0.0, ge=0.0, le=5.0)
    delivery_time: Optional[int] = Field(default=None, ge=0)
    is_active: bool = True


class RestaurantCreate(RestaurantBase):
    owner_id: Optional[UUID] = None


class RestaurantUpdate(BaseModel):
    name: Optional[constr(min_length=1, max_length=120)] = None
    description: Optional[str] = None
    cuisine: Optional[constr(max_length=120)] = None
    address: Optional[constr(min_length=1, max_length=255)] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rating: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    delivery_time: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class RestaurantRead(RestaurantBase):
    id: UUID
    owner_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderCounts(BaseModel):
    incoming: int = 0
    active: int = 0
    completed: int = 0
    cancelled: int = 0
    total: int = 0


class OrderItemBrief(BaseModel):
    id: UUID
    name: str
    price: float
    quantity: int

    class Config:
        from_attributes = True


class DashboardOrderRead(BaseModel):
    """Simplified order read for the dashboard."""
    id: UUID
    customer_id: UUID
    restaurant_id: UUID
    delivery_address_text: Optional[str] = None
    subtotal: float
    delivery_fee: float
    gst: float
    total_amount: float
    status: str
    items: List[OrderItemBrief] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RestaurantDashboard(BaseModel):
    restaurants: List[RestaurantRead]
    order_counts: OrderCounts
    incoming_orders: List[DashboardOrderRead] = []
    active_orders: List[DashboardOrderRead] = []
    completed_orders: List[DashboardOrderRead] = []
    cancelled_orders: List[DashboardOrderRead] = []
