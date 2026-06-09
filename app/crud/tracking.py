import math
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from app.db.models.order import Order
from app.services.distance import haversine_km
from app.db.models.driver_location import DriverLocation


RADIUS_EARTH_KM = 6371.0


def _update_eta(order: Order) -> None:
    if order.route_distance_km is None:
        return
    speed_kmh = 25.0
    eta_hours = order.route_distance_km / max(speed_kmh, 1.0)
    order.eta_minutes = round(eta_hours * 60, 2)


def update_tracking(db: Session, order_id: UUID, payload: dict) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise ValueError("Order not found.")

    if "partner_lat" in payload and "partner_lng" in payload:
        order.partner_lat = payload["partner_lat"]
        order.partner_lng = payload["partner_lng"]
        order.last_location_updated_at = datetime.utcnow()
        # persist driver location ping
        try:
            dl = DriverLocation(driver_id=order.delivery_partner_id, latitude=order.partner_lat, longitude=order.partner_lng)
            db.add(dl)
        except Exception:
            # non-fatal: continue
            pass

    if "delivery_lat" in payload and "delivery_lng" in payload:
        order.delivery_lat = payload["delivery_lat"]
        order.delivery_lng = payload["delivery_lng"]

    if "partner_lat" in payload and "partner_lng" in payload and order.delivery_lat is not None and order.delivery_lng is not None:
        order.route_distance_km = round(
            haversine_km(order.partner_lat, order.partner_lng, order.delivery_lat, order.delivery_lng),
            2,
        )
        _update_eta(order)

    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_tracking(db: Session, order_id: UUID) -> Optional[Order]:
    return db.query(Order).filter(Order.id == order_id).first()
