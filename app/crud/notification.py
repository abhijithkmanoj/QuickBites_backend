from typing import List, Optional, Tuple
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.models.notification import Notification


def create_notification(db: Session, user_id: uuid.UUID, *, type: Optional[str] = None, title: Optional[str] = None, body: Optional[str] = None, data: Optional[dict] = None, order_id: Optional[uuid.UUID] = None) -> Notification:
    notif = Notification(
        user_id=user_id,
        type=type,
        title=title,
        body=body,
        data=data,
        order_id=order_id,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def list_user_notifications(db: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100) -> List[Notification]:
    return db.query(Notification).filter(Notification.user_id == user_id).order_by(Notification.created_at.desc()).offset(skip).limit(limit).all()


def mark_notification_read(db: Session, user_id: uuid.UUID, notification_id: uuid.UUID) -> Optional[Notification]:
    notif = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == user_id).first()
    if not notif:
        return None
    notif.read = True
    notif.updated_at = datetime.utcnow()
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


def mark_all_read(db: Session, user_id: uuid.UUID) -> int:
    res = db.query(Notification).filter(Notification.user_id == user_id, Notification.read == False).update({"read": True})
    db.commit()
    return res
