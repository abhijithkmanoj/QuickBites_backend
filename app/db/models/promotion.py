from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.base import Base
import uuid


class Promotion(Base):
    __tablename__ = 'promotions'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(100), unique=True, nullable=False)
    description = Column(String(500), nullable=True)
    discount_amount = Column(Integer, nullable=True)  # in paise
    discount_percent = Column(Integer, nullable=True)
    is_active = Column(Boolean, default=True)
    scheduled_start_at = Column(DateTime, nullable=True)
    scheduled_end_at = Column(DateTime, nullable=True)
    target_segment = Column(String(50), nullable=True)
    is_stackable = Column(Boolean, default=False)
    stack_priority = Column(Integer, default=0)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())


class PromotionUsage(Base):
    __tablename__ = 'promotion_usages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    promotion_id = Column(UUID(as_uuid=True), ForeignKey('promotions.id'), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    order_id = Column(UUID(as_uuid=True), nullable=True)
    discount_applied = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
