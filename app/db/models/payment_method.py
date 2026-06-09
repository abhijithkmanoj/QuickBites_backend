import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.types import GUID


class PaymentMethod(Base):
    __tablename__ = "payment_methods"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, nullable=False)
    stripe_payment_method_id = Column(String(255), nullable=False, unique=True)
    stripe_customer_id = Column(String(255), nullable=True)
    type = Column(String(50), nullable=True)
    card_brand = Column(String(50), nullable=True)
    card_last4 = Column(String(4), nullable=True)
    card_exp_month = Column(Integer, nullable=True)
    card_exp_year = Column(Integer, nullable=True)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
