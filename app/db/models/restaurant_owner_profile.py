import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.types import GUID


class RestaurantOwnerProfile(Base):
    __tablename__ = "restaurant_owner_profiles"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    business_name = Column(String(255), nullable=False)
    gstin = Column(String(15), nullable=True)
    fssai_license_number = Column(String(14), nullable=True)
    bank_account_number = Column(String(50), nullable=True)
    ifsc_code = Column(String(11), nullable=True)
    verification_status = Column(String(20), nullable=False, default="pending")  # pending / approved / rejected
    rejection_reason = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="owner_profile")

    class Config:
        from_attributes = True