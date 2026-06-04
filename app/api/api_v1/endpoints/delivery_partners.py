from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_roles
from app.core.roles import Role
from app.crud.delivery_partner import (
    create_delivery_partner,
    get_delivery_partner,
    get_delivery_partner_by_user,
    update_delivery_partner,
    update_verification_status,
)
from app.crud.delivery_assignment import (
    assign_delivery_partner_to_order,
    get_available_partners_near_restaurant,
)
from app.crud.order import get_order, update_order_status
from app.crud.tracking import update_tracking, get_tracking
from app.db.models.order import Order
from app.db.models.user import User
from app.schemas.delivery_partner import (
    DeliveryPartnerCreate,
    DeliveryPartnerRead,
    DeliveryPartnerUpdate,
    VerificationStatus,
)
from app.schemas.order import OrderRead
from app.services import realtime as realtime_service

router = APIRouter()


@router.post(
    "/onboard",
    response_model=DeliveryPartnerRead,
    status_code=status.HTTP_201_CREATED,
)
def onboard_delivery_partner(
    profile_in: DeliveryPartnerCreate,
    current_user: User = Depends(require_roles(Role.delivery_partner)),
    db: Session = Depends(get_db),
):
    existing = get_delivery_partner_by_user(db, current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted onboarding details.",
        )
    partner = create_delivery_partner(db, current_user.id, profile_in)
    return partner


@router.get(
    "/profile",
    response_model=DeliveryPartnerRead,
)
def read_delivery_partner_profile(
    current_user: User = Depends(require_roles(Role.delivery_partner)),
    db: Session = Depends(get_db),
):
    partner = get_delivery_partner_by_user(db, current_user.id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery partner profile not found. Please complete onboarding.",
        )
    return partner


@router.put(
    "/profile",
    response_model=DeliveryPartnerRead,
)
def update_delivery_partner_profile(
    profile_in: DeliveryPartnerUpdate,
    current_user: User = Depends(require_roles(Role.delivery_partner)),
    db: Session = Depends(get_db),
):
    partner = get_delivery_partner_by_user(db, current_user.id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery partner profile not found.",
        )
    return update_delivery_partner(db, partner, profile_in)


@router.put(
    "/availability",
    response_model=DeliveryPartnerRead,
)
def update_availability(
    is_available: bool = Body(..., embed=True),
    current_user: User = Depends(require_roles(Role.delivery_partner)),
    db: Session = Depends(get_db),
):
    partner = get_delivery_partner_by_user(db, current_user.id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery partner profile not found.",
        )
    update_data = DeliveryPartnerUpdate(is_available=is_available)
    return update_delivery_partner(db, partner, update_data)


@router.get(
    "/available-orders",
    response_model=List[OrderRead],
)
def get_available_orders(
    current_user: User = Depends(require_roles(Role.delivery_partner)),
    db: Session = Depends(get_db),
):
    orders = (
        db.query(Order)
        .filter(Order.status == "ready_for_pickup")
        .order_by(Order.created_at.desc())
        .limit(20)
        .all()
    )
    return orders


@router.post(
    "/assignments/{order_id}/accept",
    response_model=OrderRead,
)
def accept_delivery(
    order_id: str,
    current_user: User = Depends(require_roles(Role.delivery_partner)),
    db: Session = Depends(get_db),
):
    partner = get_delivery_partner_by_user(db, current_user.id)
    if not partner or partner.verification_status != VerificationStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not verified. You cannot accept orders yet.",
        )
    try:
        order, assigned_partner = assign_delivery_partner_to_order(db, order_id)
        realtime_service.emit_order_assigned(order.id, assigned_partner.id)
        return order
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/assignments/{order_id}/picked-up",
    response_model=OrderRead,
)
def mark_picked_up(
    order_id: str,
    current_user: User = Depends(require_roles(Role.delivery_partner)),
    db: Session = Depends(get_db),
):
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    partner = get_delivery_partner_by_user(db, current_user.id)
    if not partner or (order.delivery_partner_id and order.delivery_partner_id != partner.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your order.")
    update_order_status(db, order, "picked_up")
    return order


@router.put(
    "/assignments/{order_id}/delivered",
    response_model=OrderRead,
)
def mark_delivered(
    order_id: str,
    current_user: User = Depends(require_roles(Role.delivery_partner)),
    db: Session = Depends(get_db),
):
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    partner = get_delivery_partner_by_user(db, current_user.id)
    if not partner or (order.delivery_partner_id and order.delivery_partner_id != partner.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your order.")
    update_order_status(db, order, "delivered")
    realtime_service.emit_order_delivered(order.id)
    return order


@router.post(
    "/location",
    response_model=DeliveryPartnerRead,
)
def update_location(
    latitude: float = Body(..., embed=True),
    longitude: float = Body(..., embed=True),
    current_user: User = Depends(require_roles(Role.delivery_partner)),
    db: Session = Depends(get_db),
):
    partner = get_delivery_partner_by_user(db, current_user.id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery partner profile not found.",
        )
    update_data = DeliveryPartnerUpdate(current_latitude=latitude, current_longitude=longitude)
    return update_delivery_partner(db, partner, update_data)