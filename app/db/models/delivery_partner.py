
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class DeliveryPartner(Base):
    __tablename__ = "delivery_partners"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    vehicle_type = Column(String(120), nullable=False)
    license_number = Column(String(120), nullable=False)
    aadhar_number = Column(String(12), nullable=True)
    license_image_url = Column(String(255), nullable=True)
    profile_image_url = Column(String(255), nullable=True)
    vehicle_number = Column(String(20), nullable=True)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    rating = Column(Float, nullable=False, default=0.0)
    is_available = Column(Boolean, nullable=False, default=True)
    verification_status = Column(String(20), nullable=False, default="pending")  # pending / approved / rejected
    rejection_reason = Column(Text, nullable=True)
    total_deliveries = Column(Float, nullable=False, default=0)
    earnings_today = Column(Float, nullable=False, default=0.0)
    earnings_total = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="delivery_partner")

