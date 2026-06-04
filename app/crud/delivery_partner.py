import uuid
from datetime import datetime
from sqlalchemy.orm import Session

from app.db.models.delivery_partner import DeliveryPartner
from app.schemas.delivery_partner import DeliveryPartnerCreate, DeliveryPartnerUpdate, VerificationStatus


def get_delivery_partner_by_user(db: Session, user_id: str | uuid.UUID) -> DeliveryPartner | None:
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except Exception:
            pass
    return db.query(DeliveryPartner).filter(DeliveryPartner.user_id == user_id).first()


def get_delivery_partner(db: Session, delivery_partner_id: str | uuid.UUID) -> DeliveryPartner | None:
    if isinstance(delivery_partner_id, str):
        try:
            delivery_partner_id = uuid.UUID(delivery_partner_id)
        except Exception:
            pass
    return db.query(DeliveryPartner).filter(DeliveryPartner.id == delivery_partner_id).first()


def create_delivery_partner(db: Session, user_id: str | uuid.UUID, partner_in: DeliveryPartnerCreate) -> DeliveryPartner:
    if isinstance(user_id, str):
        try:
            user_id = uuid.UUID(user_id)
        except Exception:
            pass
    partner = DeliveryPartner(
        user_id=user_id,
        vehicle_type=partner_in.vehicle_type,
        license_number=partner_in.license_number,
        is_available=partner_in.is_available if partner_in.is_available is not None else True,
        verification_status=VerificationStatus.pending.value,
    )
    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


def update_delivery_partner(db: Session, partner: DeliveryPartner, partner_in: DeliveryPartnerUpdate) -> DeliveryPartner:
    if partner_in.vehicle_type is not None:
        partner.vehicle_type = partner_in.vehicle_type
    if partner_in.license_number is not None:
        partner.license_number = partner_in.license_number
    if partner_in.aadhar_number is not None:
        partner.aadhar_number = partner_in.aadhar_number
    if partner_in.license_image_url is not None:
        partner.license_image_url = partner_in.license_image_url
    if partner_in.profile_image_url is not None:
        partner.profile_image_url = partner_in.profile_image_url
    if partner_in.vehicle_number is not None:
        partner.vehicle_number = partner_in.vehicle_number
    if partner_in.current_latitude is not None:
        partner.current_latitude = partner_in.current_latitude
    if partner_in.current_longitude is not None:
        partner.current_longitude = partner_in.current_longitude
    if partner_in.is_available is not None:
        partner.is_available = partner_in.is_available

    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner


def update_verification_status(
    db: Session,
    partner: DeliveryPartner,
    status: VerificationStatus,
    rejection_reason: str | None = None,
) -> DeliveryPartner:
    partner.verification_status = status
    partner.rejection_reason = rejection_reason
    if status == VerificationStatus.approved:
        partner.verified_at = datetime.utcnow()
    else:
        partner.verified_at = None

    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner
