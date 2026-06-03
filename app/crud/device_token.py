import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models.device_token import DeviceToken
from app.schemas.device_token import DeviceTokenCreate


def register_device_token(db: Session, user_id: uuid.UUID, token_in: DeviceTokenCreate) -> DeviceToken:
    existing = db.query(DeviceToken).filter(DeviceToken.token == token_in.token).first()
    if existing:
        existing.user_id = user_id
        existing.platform = token_in.platform
        existing.updated_at = datetime.utcnow()
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    device_token = DeviceToken(
        user_id=user_id,
        token=token_in.token,
        platform=token_in.platform,
    )
    db.add(device_token)
    db.commit()
    db.refresh(device_token)
    return device_token


def get_user_device_tokens(db: Session, user_id: uuid.UUID) -> List[DeviceToken]:
    return db.query(DeviceToken).filter(DeviceToken.user_id == user_id).all()


def delete_device_token(db: Session, token: str) -> None:
    db.query(DeviceToken).filter(DeviceToken.token == token).delete()
    db.commit()
