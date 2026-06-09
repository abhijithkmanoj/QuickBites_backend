import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Boolean, ForeignKey
from app.db.base import Base
from app.db.types import GUID


class LoyaltyAccount(Base):
    __tablename__ = "loyalty_accounts"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    points = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Reward(Base):
    __tablename__ = "rewards"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    code = Column(String(64), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    points_cost = Column(Integer, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RewardRedemption(Base):
    __tablename__ = "reward_redemptions"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reward_id = Column(GUID, ForeignKey("rewards.id", ondelete="SET NULL"), nullable=False)
    points_spent = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), nullable=False, default="pending")
