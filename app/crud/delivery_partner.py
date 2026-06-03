import uuid
from sqlalchemy.orm import Session

from app.db.models.delivery_partner import DeliveryPartner
from app.schemas.delivery_partner import DeliveryPartnerCreate, DeliveryPartnerUpdate


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
    if partner_in.is_available is not None:
        partner.is_available = partner_in.is_available

    db.add(partner)
    db.commit()
    db.refresh(partner)
    return partner
