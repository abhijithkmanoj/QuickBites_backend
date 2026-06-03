"""CRUD operations for UserActivity."""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.user_activity import UserActivity


def list_activities(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[UserActivity], int]:
    """Get paginated activity log for a user."""
    query = db.query(UserActivity).filter(UserActivity.user_id == user_id).order_by(UserActivity.created_at.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return items, total


def get_activity(db: Session, activity_id: UUID) -> Optional[UserActivity]:
    """Get a single activity record."""
    return db.query(UserActivity).filter(UserActivity.id == activity_id).first()


def create_activity(
    db: Session,
    user_id: UUID,
    activity_type: str,
    activity_data: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> UserActivity:
    """Create a new activity record."""
    activity = UserActivity(
        user_id=user_id,
        activity_type=activity_type,
        activity_data=activity_data,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def delete_activity(db: Session, activity_id: UUID) -> bool:
    """Delete a single activity record."""
    activity = db.query(UserActivity).filter(UserActivity.id == activity_id).first()
    if not activity:
        return False
    db.delete(activity)
    db.commit()
    return True


def clear_old_activities(
    db: Session,
    user_id: UUID,
    days_to_keep: int = 90,
) -> int:
    """Clear activity records older than specified days for a user."""
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    deleted = db.query(UserActivity).filter(
        UserActivity.user_id == user_id,
        UserActivity.created_at < cutoff_date,
    ).delete()
    db.commit()
    return deleted
