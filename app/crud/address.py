import uuid
from typing import List
from sqlalchemy.orm import Session
from app.db.models.address import Address
from app.schemas.address import AddressCreate, AddressUpdate


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
        is_default=address_in.is_default,
    )
    db.add(address)
    db.commit()
    db.refresh(address)
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
    return address


def delete_address(db: Session, address: Address) -> None:
    db.delete(address)
    db.commit()
