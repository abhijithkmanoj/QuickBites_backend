from typing import Callable, List

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.roles import Role
from app.core.security import decode_token
from app.db.models.user import User
from app.db.session import get_db as get_db_session
from app.crud.user import get_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_settings():
    return settings


def get_db():
    yield from get_db_session()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        user_id = payload.get("sub")
        if user_id is None:
            raise ValueError("Missing subject")
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = get_user(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Inactive user.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


def require_roles(*allowed_roles: Role) -> Callable:
    allowed_values: List[str] = [role.value for role in allowed_roles]

    def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_values:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions.",
            )
        return current_user

    return dependency


def get_current_active_admin(current_user: User = Depends(get_current_active_user)) -> User:
    if current_user.role != Role.admin.value:
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required.",
        )
    return current_user
