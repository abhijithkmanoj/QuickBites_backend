
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.types import GUID


class Review(Base):
    __tablename__ = "reviews"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    order_id = Column(GUID, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    restaurant_id = Column(GUID, ForeignKey("restaurants.id", ondelete="CASCADE"), nullable=False, index=True)
    delivery_partner_id = Column(GUID, ForeignKey("delivery_partners.id", ondelete="SET NULL"), nullable=True, index=True)
    rating = Column(Integer, nullable=False)
    review_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order")
    restaurant = relationship("Restaurant")
    delivery_partner = relationship("DeliveryPartner")

