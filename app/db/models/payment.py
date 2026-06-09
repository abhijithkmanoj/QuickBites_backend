
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.types import GUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import BigInteger


class Payment(Base):
    __tablename__ = "payments"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    order_id = Column(GUID, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Float, nullable=False, default=0.0)
    method = Column(String(50), nullable=False, default="cod")
    status = Column(String(50), nullable=False, default="pending")
    stripe_payment_intent_id = Column(String(255), nullable=True, unique=False, index=True)
    currency = Column(String(3), nullable=True, default="inr")
    stripe_customer_id = Column(String(255), nullable=True)
    metadata_json = Column(JSONB, nullable=True)
    amount_cents = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    order = relationship("Order", back_populates="payment")
    user = relationship("User")

