import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, String, Text, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.types import GUID


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=True, index=True)
    title = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)
    order_id = Column(GUID, nullable=True, index=True)
    data = Column(JSON, nullable=True)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
