
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.types import GUID


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(GUID, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(120), nullable=True)
    name = Column(String(120), nullable=False, index=True)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False, default=0.0)
    image_url = Column(String(255), nullable=True)
    is_veg = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="menu_items")

