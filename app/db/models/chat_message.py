import uuid
from datetime import datetime
from sqlalchemy import Column, Text, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    sender_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    sender_role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    message_type = Column(String(20), nullable=False, default='text')
    is_read = Column(Boolean, nullable=False, default=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
