from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, require_roles, get_db
from app.core.roles import Role
from app.crud.restaurant_owner_profile import (
    create_owner_profile,
    get_owner_profile,
    update_owner_profile,
)
from app.db.models.user import User
from app.schemas.restaurant_owner_profile import (
    RestaurantOwnerProfileCreate,
    RestaurantOwnerProfileRead,
    RestaurantOwnerProfileUpdate,
    VerificationStatusRead,
    VerificationStatus,
)

router = APIRouter()


@router.post(
    "/onboard",
    response_model=RestaurantOwnerProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit restaurant owner onboarding details",
)
def onboard_owner(
    profile_in: RestaurantOwnerProfileCreate,
    current_user: User = Depends(require_roles(Role.restaurant_owner)),
    db: Session = Depends(get_db),
):
    existing = get_owner_profile(db, current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted onboarding details.",
        )
    return create_owner_profile(db, current_user.id, profile_in)


@router.get(
    "/profile",
    response_model=RestaurantOwnerProfileRead,
    summary="Get restaurant owner profile",
)
def read_owner_profile(
    current_user: User = Depends(require_roles(Role.restaurant_owner)),
    db: Session = Depends(get_db),
):
    profile = get_owner_profile(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner profile not found. Please complete onboarding.",
        )
    return profile


@router.put(
    "/profile",
    response_model=RestaurantOwnerProfileRead,
    summary="Update restaurant owner profile",
)
def update_owner_profile_endpoint(
    profile_in: RestaurantOwnerProfileUpdate,
    current_user: User = Depends(require_roles(Role.restaurant_owner)),
    db: Session = Depends(get_db),
):
    profile = get_owner_profile(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner profile not found. Please complete onboarding.",
        )
    return update_owner_profile(db, profile, profile_in)


@router.get(
    "/verification-status",
    response_model=VerificationStatusRead,
    summary="Check owner verification status",
)
def get_verification_status(
    current_user: User = Depends(require_roles(Role.restaurant_owner)),
    db: Session = Depends(get_db),
):
    profile = get_owner_profile(db, current_user.id)
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner profile not found. Please complete onboarding.",
        )
    return VerificationStatusRead(
        status=VerificationStatus(profile.verification_status),
        rejection_reason=profile.rejection_reason,
    )