import uuid
from typing import List
from sqlalchemy.orm import Session
from app.db.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate
from app.services import geocoding
import logging

logger = logging.getLogger(__name__)


def _parse_uuid(value: str | uuid.UUID) -> uuid.UUID | str:
    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            return value
    return value


def get_address(db: Session, address_id: str | uuid.UUID) -> Address | None:
    return db.query(Address).filter(Address.id == _parse_uuid(address_id)).first()


def get_user_addresses(db: Session, user_id: str | uuid.UUID) -> List[Address]:
    return (
        db.query(Address)
        .filter(Address.user_id == _parse_uuid(user_id))
        .order_by(Address.is_default.desc(), Address.created_at.desc())
        .all()
    )


def get_default_address(db: Session, user_id: str | uuid.UUID) -> Address | None:
    return (
        db.query(Address)
        .filter(Address.user_id == _parse_uuid(user_id), Address.is_default == True)
        .first()
    )


def _unset_other_defaults(db: Session, user_id: str | uuid.UUID, exclude_id: str | uuid.UUID | None = None) -> None:
    """Unset is_default on all other addresses for this user."""
    query = db.query(Address).filter(
        Address.user_id == _parse_uuid(user_id),
        Address.is_default == True,
    )
    if exclude_id:
        query = query.filter(Address.id != _parse_uuid(exclude_id))
    for addr in query.all():
        addr.is_default = False
        db.add(addr)


def create_address(db: Session, user_id: str | uuid.UUID, address_in: AddressCreate) -> Address:
    if address_in.is_default:
        _unset_other_defaults(db, user_id)

    address = Address(
        user_id=_parse_uuid(user_id),
        street=address_in.street,
        city=address_in.city,
        state=address_in.state,
        postal_code=address_in.postal_code,
        phone=address_in.phone,
        landmark=address_in.landmark,
        address_line2=getattr(address_in, "address_line2", None),
        unit=getattr(address_in, "unit", None),
        is_default=address_in.is_default,
    )
    db.add(address)
    db.commit()
    db.refresh(address)

    # Best-effort geocode: do not let failures block address creation
    try:
        full_address = f"{address.street}, {address.city}, {address.state}, {address.postal_code}"
        geo = geocoding.geocode_address(full_address)
        if geo and geo.get("lat") and geo.get("lng"):
            address.latitude = geo.get("lat")
            address.longitude = geo.get("lng")
            address.formatted_address = geo.get("formatted_address")
            address.place_id = geo.get("place_id")
            db.add(address)
            db.commit()
            db.refresh(address)
    except Exception as exc:
        logger.exception("Geocoding failed for address %s: %s", getattr(address, "id", "?"), exc)

    return address


def update_address(db: Session, address: Address, address_in: AddressUpdate) -> Address:
    update_data = address_in.dict(exclude_unset=True)

    if update_data.get("is_default"):
        _unset_other_defaults(db, address.user_id, exclude_id=address.id)

    for field, value in update_data.items():
        setattr(address, field, value)
    db.add(address)
    db.commit()
    db.refresh(address)

    # Best-effort geocode when address fields changed
    try:
        if any(k in update_data for k in ("street", "city", "state", "postal_code")):
            full_address = f"{address.street}, {address.city}, {address.state}, {address.postal_code}"
            geo = geocoding.geocode_address(full_address)
            if geo and geo.get("lat") and geo.get("lng"):
                address.latitude = geo.get("lat")
                address.longitude = geo.get("lng")
                address.formatted_address = geo.get("formatted_address")
                address.place_id = geo.get("place_id")
                db.add(address)
                db.commit()
                db.refresh(address)
    except Exception as exc:
        logger.exception("Geocoding failed on update for address %s: %s", getattr(address, "id", "?"), exc)

    return address


def delete_address(db: Session, address: Address) -> None:
    db.delete(address)
    db.commit()
