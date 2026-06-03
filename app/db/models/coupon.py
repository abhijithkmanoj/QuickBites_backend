import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String, Float, Integer, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.types import GUID


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    code = Column(String(50), unique=True, nullable=False, index=True)
    discount_type = Column(String(20), nullable=False, default="percentage")
    discount_value = Column(Float, nullable=False)
    usage_limit = Column(Integer, nullable=True)
    used_count = Column(Integer, nullable=False, default=0)
    expiry_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
