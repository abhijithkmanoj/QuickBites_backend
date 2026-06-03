from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user
from app.crud.device_token import register_device_token, get_user_device_tokens, delete_device_token
from app.db.models.user import User
from app.schemas.device_token import DeviceTokenCreate, DeviceTokenRead

router = APIRouter()


@router.post("/register", response_model=DeviceTokenRead, status_code=status.HTTP_201_CREATED, summary="Register FCM device token")
def register_token(
    token_in: DeviceTokenCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return register_device_token(db, current_user.id, token_in)


@router.get("/my-tokens", response_model=list[DeviceTokenRead], summary="Get my device tokens")
def list_tokens(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    return get_user_device_tokens(db, current_user.id)


@router.delete("/{token}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a device token")
def remove_token(
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    delete_device_token(db, token)
    return None
