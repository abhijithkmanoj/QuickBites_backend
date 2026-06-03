from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User


def create_refresh_token(db: Session, user: User, jti: str, expires_at: datetime) -> RefreshToken:
    token = RefreshToken(
        jti=jti,
        user_id=user.id,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def get_refresh_token(db: Session, jti: str) -> Optional[RefreshToken]:
    return db.query(RefreshToken).filter(RefreshToken.jti == jti).first()


def revoke_refresh_token(db: Session, token: RefreshToken, replaced_by_jti: Optional[str] = None) -> RefreshToken:
    token.revoked = True
    token.revoked_at = datetime.utcnow()
    token.replaced_by_jti = replaced_by_jti
    db.add(token)
    db.commit()
    db.refresh(token)
    return token


def prune_expired_refresh_tokens(db: Session) -> None:
    db.query(RefreshToken).filter(
        RefreshToken.expires_at < datetime.utcnow(),
        RefreshToken.revoked == False,
    ).update({"revoked": True, "revoked_at": datetime.utcnow()})
    db.commit()
