import uuid
from datetime import datetime
from math import radians, cos, sin, asin, sqrt
from typing import Optional
from sqlalchemy.orm import Session

from app.db.models.delivery_partner import DeliveryPartner
from app.db.models.restaurant import Restaurant
from app.db.models.order import Order


def _parse_uuid(value):
    if isinstance(value, uuid.UUID):
        return value
    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            return value
    return value


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in kilometers."""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return 6371 * c


def get_available_partners_near_restaurant(
    db: Session,
    restaurant_id: uuid.UUID,
    radius_km: float = 20.0,
    limit: int = 10,
) -> list[DeliveryPartner]:
    restaurant = db.query(Restaurant).filter(Restaurant.id == _parse_uuid(restaurant_id)).first()
    if not restaurant or restaurant.latitude is None or restaurant.longitude is None:
        return []

    partners = db.query(DeliveryPartner).filter(DeliveryPartner.is_available.is_(True)).all()

    scored = []
    for partner in partners:
        user = partner.user
        if not user:
            continue
        scored.append((partner, user))

    scored.sort(key=lambda item: item[0].rating, reverse=True)
    return [partner for partner, _ in scored[:limit]]


def assign_delivery_partner(db: Session, order: Order, partner: DeliveryPartner) -> Order:
    if order.delivery_partner_id is not None:
        raise ValueError("Order already has an assigned delivery partner.")

    order.delivery_partner_id = partner.id
    order.assigned_at = datetime.utcnow()
    partner.is_available = False

    db.add(order)
    db.add(partner)
    db.commit()
    db.refresh(order)
    return order


def assign_delivery_partner_to_order(
    db: Session,
    order_id: uuid.UUID,
) -> tuple[Order, DeliveryPartner]:
    parsed_id = _parse_uuid(order_id)
    order = db.query(Order).filter(Order.id == parsed_id).first()
    if not order:
        raise ValueError("Order not found.")

    if order.delivery_partner_id is not None:
        raise ValueError("Order already has an assigned delivery partner.")

    candidates = get_available_partners_near_restaurant(
        db,
        restaurant_id=order.restaurant_id,
        radius_km=20.0,
        limit=10,
    )

    if not candidates:
        raise ValueError("No available delivery partners found nearby.")

    partner = candidates[0]
    assigned_order = assign_delivery_partner(db, order, partner)
    return assigned_order, partner
