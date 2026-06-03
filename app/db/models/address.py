
import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.types import GUID


class Address(Base):
    __tablename__ = "addresses"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    street = Column(String(255), nullable=False)
    city = Column(String(120), nullable=False)
    state = Column(String(120), nullable=False)
    postal_code = Column(String(20), nullable=False)
    phone = Column(String(20), nullable=True)
    landmark = Column(String(255), nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="addresses")

