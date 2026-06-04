from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db, require_roles
from app.core.config import settings
from app.core.roles import Role, ALL_ROLES
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.crud.token import (
    create_refresh_token as create_refresh_token_record,
    get_refresh_token,
    revoke_refresh_token,
)
from app.crud.user import authenticate_user, create_user, get_user_by_email, get_user
from app.db.models.user import User
from app.schemas.user import (
    Token,
    TokenRefreshRequest,
    UserCreate,
    UserRead,
)
from app.services.notifications import EmailService

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )
    # Public registration: only allow customer or restaurant_owner roles
    # Admin and delivery_partner roles require separate onboarding flows
    allowed_roles = [Role.customer.value, Role.restaurant_owner.value]
    if user_in.role not in allowed_roles:
        user_in.role = Role.customer
    user = create_user(db, user_in)
    try:
        EmailService.send_registration_email(user.email, user.name)
    except Exception:
        pass
    return user


@router.post("/login", response_model=Token)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(subject=str(user.id), expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token, refresh_jti = create_refresh_token(subject=str(user.id))
    refresh_expires_at = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    create_refresh_token_record(db, user, refresh_jti, datetime.utcnow() + refresh_expires_at)
    # Stamp last active
    user.last_active_at = datetime.utcnow()
    db.add(user)
    db.commit()
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_COOKIE_MAX_AGE,
        path="/",
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    response: Response,
    body: Optional[TokenRefreshRequest] = None,
    refresh_token_cookie: Optional[str] = Cookie(default=None, alias=settings.REFRESH_TOKEN_COOKIE_NAME),
    db: Session = Depends(get_db),
):
    token_value = None
    if refresh_token_cookie:
        token_value = refresh_token_cookie
    elif body is not None:
        token_value = body.refresh_token

    if not token_value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token is required.",
        )

    try:
        payload = decode_token(token_value)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token_jti = payload.get("jti")
        user_id = payload.get("sub")
        if token_jti is None or user_id is None:
            raise ValueError
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_record = get_refresh_token(db, token_jti)
    if not token_record or token_record.revoked or token_record.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is no longer valid.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or invalid user.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id))
    new_refresh_token, new_refresh_jti = create_refresh_token(subject=str(user.id))
    revoke_refresh_token(db, token_record, replaced_by_jti=new_refresh_jti)
    create_refresh_token_record(db, user, new_refresh_jti, datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    response.set_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        value=new_refresh_token,
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_COOKIE_MAX_AGE,
        path="/",
    )
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@router.post("/logout")
def logout(
    response: Response,
    refresh_token_cookie: Optional[str] = Cookie(default=None, alias=settings.REFRESH_TOKEN_COOKIE_NAME),
    db: Session = Depends(get_db),
):
    if refresh_token_cookie:
        try:
            payload = decode_token(refresh_token_cookie)
            token_jti = payload.get("jti")
            if token_jti:
                token_record = get_refresh_token(db, token_jti)
                if token_record and not token_record.revoked:
                    revoke_refresh_token(db, token_record)
        except Exception:
            pass

    response.delete_cookie(
        key=settings.REFRESH_TOKEN_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=not settings.DEBUG,
        samesite="lax",
    )
    return {"message": "Logout successful."}


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.get("/admin-check")
def admin_check(current_user: User = Depends(require_roles(Role.admin))):
    return {"message": "Admin access granted.", "email": current_user.email}
