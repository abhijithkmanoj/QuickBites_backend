import uuid
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base import Base
from app.db.types import GUID


class User(Base):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    phone = Column(String(20), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="customer")
    # Enhanced profile fields
    profile_image_url = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(20), nullable=True)
    language_preference = Column(String(10), nullable=True, default='en')
    notification_preference = Column(JSON, nullable=True)
    privacy_settings = Column(JSON, nullable=True)
    theme_preference = Column(String(20), nullable=True, default='system')
    last_active_at = Column(DateTime, nullable=True)
    profile_image = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    refresh_tokens = relationship(
        "RefreshToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    restaurants = relationship(
        "Restaurant",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    addresses = relationship(
        "Address",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    orders = relationship(
        "Order",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    delivery_partner = relationship(
        "DeliveryPartner",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    device_tokens = relationship(
        "DeviceToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    activities = relationship(
        "UserActivity",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    favorites = relationship(
        "UserFavorite",
        back_populates="user",
        cascade="all, delete-orphan",
    )
