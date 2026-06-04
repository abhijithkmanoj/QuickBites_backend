from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.core.security import get_password_hash, verify_password
from app.db.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    DeactivateAccountRequest,
    UserProfileUpdate,
    UserRead,
    UserSettingsUpdate,
)
from app.crud import user_activity, user_favorite
from app.db.models.order import Order
from app.db.models.address import Address

router = APIRouter()


# ─── Profile ──────────────────────────────────────────────────

@router.get("/profile", response_model=UserRead, summary="Get current user's profile")
def read_user_profile(current_user: User = Depends(get_current_active_user)):
    """Return the authenticated user's full profile."""
    return current_user


@router.put("/profile", response_model=UserRead, summary="Update user profile")
def update_user_profile(
    user_in: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update name, phone, bio, date_of_birth, or gender."""
    update_data = user_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    current_user.last_active_at = datetime.utcnow()
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


# ─── Profile image ────────────────────────────────────────────

@router.post("/profile-image", response_model=UserRead, summary="Upload profile picture")
def upload_profile_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Upload a profile picture. In production this would push to Cloudinary/S3."""
    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, WebP, and GIF images are allowed.",
        )

    # Stub: replace with real storage upload when Cloudinary is integrated
    file_url = f"https://placeholder.quickbites.app/avatars/{current_user.id}/{file.filename}"
    current_user.profile_image_url = file_url
    current_user.last_active_at = datetime.utcnow()
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/profile-image", response_model=UserRead, summary="Remove profile picture")
def remove_profile_image(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Clear the current user's profile picture."""
    current_user.profile_image_url = None
    current_user.last_active_at = datetime.utcnow()
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


# ─── Settings ─────────────────────────────────────────────────

@router.get("/settings", summary="Get user settings/preferences")
def get_user_settings(current_user: User = Depends(get_current_active_user)):
    """Return the user's notification, privacy, theme, and language preferences."""
    return {
        "notification_preference": current_user.notification_preference or {
            "order_updates": True,
            "promotions": True,
            "newsletter": False,
        },
        "privacy_settings": current_user.privacy_settings or {
            "show_profile": True,
            "show_order_history": False,
        },
        "theme_preference": current_user.theme_preference or "system",
        "language_preference": current_user.language_preference or "en",
    }


@router.put("/settings", response_model=UserRead, summary="Update user settings/preferences")
def update_user_settings(
    settings_in: UserSettingsUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update notification preferences, privacy settings, theme, or language."""
    update_data = settings_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)
    current_user.last_active_at = datetime.utcnow()
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


# ─── Security ─────────────────────────────────────────────────

@router.post("/change-password", summary="Change password")
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Verify current password then set a new one."""
    if not verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password.",
        )
    current_user.password_hash = get_password_hash(body.new_password)
    current_user.last_active_at = datetime.utcnow()
    db.add(current_user)
    db.commit()
    return {"message": "Password changed successfully."}


@router.post("/deactivate-account", summary="Deactivate account")
def deactivate_account(
    body: DeactivateAccountRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Require password confirmation then soft-deactivate the account."""
    if not verify_password(body.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect.",
        )
    current_user.is_active = False
    db.add(current_user)
    db.commit()
    return {"message": "Account deactivated successfully."}


# ─── Activity Log (Phase 15.2) ─────────────────────────────────

@router.get("/activity", summary="Get user activity log")
def get_activity_log(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return paginated activity log for the current user."""
    activities, total = user_activity.list_activities(db, current_user.id, skip, limit)
    return {
        "items": [
            {
                "id": str(a.id),
                "activity_type": a.activity_type,
                "activity_data": a.activity_data,
                "created_at": a.created_at,
            }
            for a in activities
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.delete("/activity/{activity_id}", summary="Delete single activity entry")
def delete_activity_entry(
    activity_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Delete a specific activity log entry."""
    try:
        activity_uuid = UUID(activity_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid activity ID")
    
    # Verify activity belongs to current user
    activity = db.query(user_activity.UserActivity).filter(
        user_activity.UserActivity.id == activity_uuid,
        user_activity.UserActivity.user_id == current_user.id,
    ).first()
    
    if not activity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity not found")
    
    success = user_activity.delete_activity(db, activity_uuid)
    if success:
        return {"message": "Activity deleted successfully."}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not delete activity")


@router.post("/activity/clear", summary="Clear old activity logs")
def clear_activity_logs(
    days: int = Query(90, ge=1),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Clear activity logs older than specified days (default 90)."""
    deleted_count = user_activity.clear_old_activities(db, current_user.id, days)
    return {"message": f"Deleted {deleted_count} old activity entries.", "deleted": deleted_count}


# ─── Favorites (Phase 15.2) ────────────────────────────────────

@router.get("/favorites", summary="Get user favorites")
def get_favorites(
    favorite_type: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return paginated favorites for the current user."""
    favorites, total = user_favorite.list_favorites(db, current_user.id, favorite_type, skip, limit)
    return {
        "items": [
            {
                "id": str(f.id),
                "favorite_type": f.favorite_type,
                "favorite_id": str(f.favorite_id),
                "created_at": f.created_at,
            }
            for f in favorites
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.post("/favorites/add", summary="Add to favorites")
def add_to_favorites(
    favorite_id: str = Query(...),
    favorite_type: str = Query(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Add a restaurant or menu item to favorites."""
    if favorite_type not in ["restaurant", "menu_item"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="favorite_type must be 'restaurant' or 'menu_item'",
        )
    
    try:
        fav_id = UUID(favorite_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid favorite ID")
    
    favorite = user_favorite.add_favorite(db, current_user.id, favorite_type, fav_id)
    return {
        "id": str(favorite.id),
        "favorite_type": favorite.favorite_type,
        "favorite_id": str(favorite.favorite_id),
        "created_at": favorite.created_at,
    }


@router.delete("/favorites/{favorite_id}", summary="Remove from favorites")
def remove_from_favorites(
    favorite_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Remove a favorite entry."""
    try:
        fav_id = UUID(favorite_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid favorite ID")
    
    favorite = user_favorite.get_favorite(db, fav_id)
    if not favorite or favorite.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")
    
    success = user_favorite.remove_favorite(db, fav_id)
    if success:
        return {"message": "Removed from favorites."}
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not remove favorite")


@router.get("/favorites/check/{favorite_type}/{favorite_id}", summary="Check if favorited")
def is_favorited(
    favorite_type: str,
    favorite_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Check if a restaurant or menu item is in user's favorites."""
    try:
        fav_id = UUID(favorite_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid favorite ID")
    
    is_fav = user_favorite.is_favorited(db, current_user.id, favorite_type, fav_id)
    return {"is_favorited": is_fav}


# ─── Order History (Phase 15.2) ────────────────────────────────

@router.get("/order-history", summary="Get user order history")
def get_order_history(
    status_filter: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return paginated order history for the current user with optional status filter."""
    # Orders are stored with `customer_id` on the Order model
    query = db.query(Order).filter(Order.customer_id == current_user.id)
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "items": [
            {
                "id": str(o.id),
                "restaurant_id": str(o.restaurant_id),
                "total_price": float(getattr(o, 'total_price', o.total_amount if hasattr(o, 'total_amount') else 0.0)),
                "status": o.status,
                "created_at": o.created_at,
                "updated_at": o.updated_at,
            }
            for o in orders
        ],
        "total": total,
        "skip": skip,
        "limit": limit,
    }


# ─── Saved Addresses (Phase 15.2) ──────────────────────────────

@router.get("/saved-addresses", summary="Get saved delivery addresses")
def get_saved_addresses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Return all saved delivery addresses for the current user."""
    addresses = db.query(Address).filter(Address.user_id == current_user.id).all()
    return {
        "items": [
            {
                "id": str(a.id),
                "address_type": a.address_type,
                "street": a.street,
                "city": a.city,
                "state": a.state,
                "zip_code": a.zip_code,
                "is_default": a.is_default,
                "created_at": a.created_at,
            }
            for a in addresses
        ],
        "total": len(addresses),
    }

