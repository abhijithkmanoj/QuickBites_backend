import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.restaurant_owner_profile import RestaurantOwnerProfile
from app.schemas.restaurant_owner_profile import RestaurantOwnerProfileCreate, RestaurantOwnerProfileUpdate, VerificationStatus


def get_owner_profile(db: Session, user_id: str | uuid.UUID) -> RestaurantOwnerProfile | None:
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except Exception:
            pass
    return db.query(RestaurantOwnerProfile).filter(RestaurantOwnerProfile.user_id == user_id).first()


def get_owner_profile_by_id(db: Session, profile_id: str | uuid.UUID) -> RestaurantOwnerProfile | None:
    if isinstance(profile_id, str):
        try:
            profile_id = uuid.UUID(profile_id)
        except Exception:
            pass
    return db.query(RestaurantOwnerProfile).filter(RestaurantOwnerProfile.id == profile_id).first()


def create_owner_profile(
    db: Session,
    user_id: str | uuid.UUID,
    profile_in: RestaurantOwnerProfileCreate,
) -> RestaurantOwnerProfile:
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except Exception:
            pass
    profile = RestaurantOwnerProfile(
        user_id=user_id,
        business_name=profile_in.business_name,
        gstin=profile_in.gstin,
        fssai_license_number=profile_in.fssai_license_number,
        bank_account_number=profile_in.bank_account_number,
        ifsc_code=profile_in.ifsc_code,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_owner_profile(
    db: Session,
    profile: RestaurantOwnerProfile,
    profile_in: RestaurantOwnerProfileUpdate,
) -> RestaurantOwnerProfile:
    if profile_in.business_name is not None:
        profile.business_name = profile_in.business_name
    if profile_in.gstin is not None:
        profile.gstin = profile_in.gstin
    if profile_in.fssai_license_number is not None:
        profile.fssai_license_number = profile_in.fssai_license_number
    if profile_in.bank_account_number is not None:
        profile.bank_account_number = profile_in.bank_account_number
    if profile_in.ifsc_code is not None:
        profile.ifsc_code = profile_in.ifsc_code

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_verification_status(
    db: Session,
    profile: RestaurantOwnerProfile,
    status: VerificationStatus,
    rejection_reason: str | None = None,
) -> RestaurantOwnerProfile:
    profile.verification_status = status
    profile.rejection_reason = rejection_reason
    if status == VerificationStatus.approved:
        profile.verified_at = datetime.utcnow()
    else:
        profile.verified_at = None

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile