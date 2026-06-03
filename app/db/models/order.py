
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.types import GUID


class Order(Base):
    __tablename__ = "orders"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    customer_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    restaurant_id = Column(GUID, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    address_id = Column(GUID, ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True)
    delivery_address_text = Column(Text, nullable=True)
    delivery_partner_id = Column(GUID, ForeignKey("delivery_partners.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_at = Column(DateTime, nullable=True)
    picked_up_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    subtotal = Column(Float, nullable=False, default=0.0)
    delivery_fee = Column(Float, nullable=False, default=0.0)
    gst = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    delivery_lat = Column(Float, nullable=True)
    delivery_lng = Column(Float, nullable=True)
    partner_lat = Column(Float, nullable=True)
    partner_lng = Column(Float, nullable=True)
    route_distance_km = Column(Float, nullable=True)
    eta_minutes = Column(Float, nullable=True)
    last_location_updated_at = Column(DateTime, nullable=True)

    customer = relationship("User", back_populates="orders")
    restaurant = relationship("Restaurant")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="order", uselist=False, cascade="all, delete-orphan")
    delivery_partner = relationship("DeliveryPartner")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    order_id = Column(GUID, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    menu_item_id = Column(GUID, ForeignKey("menu_items.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(120), nullable=False)
    price = Column(Float, nullable=False, default=0.0)
    quantity = Column(Integer, nullable=False, default=1)

    order = relationship("Order", back_populates="items")

