
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Float, String
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.types import GUID


class Cart(Base):
    __tablename__ = "carts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    restaurant_id = Column(GUID, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    cart_id = Column(GUID, ForeignKey("carts.id", ondelete="CASCADE"), nullable=False, index=True)
    menu_item_id = Column(GUID, ForeignKey("menu_items.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(120), nullable=False)
    price = Column(Float, nullable=False, default=0.0)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cart = relationship("Cart", back_populates="items")

