"""CRUD operations for UserFavorite."""

from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.user_favorite import UserFavorite


def add_favorite(
    db: Session,
    user_id: UUID,
    favorite_type: str,  # "restaurant" or "menu_item"
    favorite_id: UUID,
) -> UserFavorite:
    """Add an item to user's favorites. Returns existing if already favorited."""
    existing = db.query(UserFavorite).filter(
        UserFavorite.user_id == user_id,
        UserFavorite.favorite_type == favorite_type,
        UserFavorite.favorite_id == favorite_id,
    ).first()

    if existing:
        return existing

    favorite = UserFavorite(
        user_id=user_id,
        favorite_type=favorite_type,
        favorite_id=favorite_id,
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


def remove_favorite(db: Session, favorite_id: UUID) -> bool:
    """Remove a favorite item."""
    favorite = db.query(UserFavorite).filter(UserFavorite.id == favorite_id).first()
    if not favorite:
        return False
    db.delete(favorite)
    db.commit()
    return True


def list_favorites(
    db: Session,
    user_id: UUID,
    favorite_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[UserFavorite], int]:
    """Get paginated favorites for a user, optionally filtered by type."""
    query = db.query(UserFavorite).filter(UserFavorite.user_id == user_id)

    if favorite_type:
        query = query.filter(UserFavorite.favorite_type == favorite_type)

    total = query.count()
    items = query.order_by(UserFavorite.created_at.desc()).offset(skip).limit(limit).all()
    return items, total


def is_favorited(
    db: Session,
    user_id: UUID,
    favorite_type: str,
    favorite_id: UUID,
) -> bool:
    """Check if an item is favorited by the user."""
    return (
        db.query(UserFavorite)
        .filter(
            UserFavorite.user_id == user_id,
            UserFavorite.favorite_type == favorite_type,
            UserFavorite.favorite_id == favorite_id,
        )
        .first()
        is not None
    )


def get_favorite(db: Session, favorite_id: UUID) -> Optional[UserFavorite]:
    """Get a single favorite record."""
    return db.query(UserFavorite).filter(UserFavorite.id == favorite_id).first()
