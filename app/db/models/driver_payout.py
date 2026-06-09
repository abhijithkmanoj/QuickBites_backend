import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Float, Boolean
from app.db.base import Base
from app.db.types import GUID


class DriverPayout(Base):
    __tablename__ = "driver_payouts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    driver_id = Column(GUID, nullable=False, index=True)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default="inr")
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)
    metadata_raw = Column(String(1024), nullable=True)
