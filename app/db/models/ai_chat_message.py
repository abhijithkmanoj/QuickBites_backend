import uuid
from datetime import datetime
from sqlalchemy import Column, Text, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base


class AIChatMessage(Base):
    __tablename__ = 'ai_chat_messages'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
