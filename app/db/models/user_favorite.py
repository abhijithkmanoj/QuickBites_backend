
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.db.types import GUID


class UserFavorite(Base):
    """Stores user-favourited restaurants and menu items."""

    __tablename__ = "user_favorites"

    id = Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # "restaurant" or "menu_item"
    favorite_type = Column(String(20), nullable=False)
    # UUID of the restaurant or menu_item row
    favorite_id = Column(GUID, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="favorites")

    __table_args__ = (
        # one entry per (user, type, item) pair
        UniqueConstraint("user_id", "favorite_type", "favorite_id", name="uq_user_favorite"),
    )

