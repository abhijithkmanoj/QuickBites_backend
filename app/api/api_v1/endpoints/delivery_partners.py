from typing import List

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user, require_roles
from app.core.roles import Role
from app.crud.delivery_partner import (
    create_delivery_partner,
    get_delivery_partner,
    get_delivery_partner_by_user,
    update_delivery_partner,
)
from app.crud.delivery_assignment import (
    assign_delivery_partner_to_order,
    get_available_partners_near_restaurant,
)
from app.crud.tracking import update_tracking, get_tracking
from app.db.models.user import User
from app.schemas.delivery_partner import (
    DeliveryPartnerCreate,
    DeliveryPartnerRead,
    DeliveryPartnerUpdate,
)
from app.schemas.order import OrderRead
from app.services import realtime as realtime_service

router = APIRouter()


@router.post(
    "/register",
    response_model=DeliveryPartnerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register as a delivery partner",
)
def register_delivery_partner(
    partner_in: DeliveryPartnerCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    existing = get_delivery_partner_by_user(db, current_user.id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already registered as a delivery partner.",
        )
    return create_delivery_partner(db, current_user.id, partner_in)


@router.get(
    "/profile",
    response_model=DeliveryPartnerRead,
    summary="Get current delivery partner profile",
)
def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    partner = get_delivery_partner_by_user(db, current_user.id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery partner profile not found.",
        )
    return partner


@router.put(
    "/availability",
    response_model=DeliveryPartnerRead,
    summary="Update delivery partner availability",
)
def update_availability(
    availability_in: DeliveryPartnerUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    partner = get_delivery_partner_by_user(db, current_user.id)
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery partner profile not found.",
        )
    return update_delivery_partner(db, partner, availability_in)


@router.get(
    "/available",
    response_model=List[DeliveryPartnerRead],
    summary="Get available delivery partners near a restaurant",
)
def list_available_partners(
    restaurant_id: str = Query(..., description="Restaurant ID to find partners near."),
    radius_km: float = Query(20.0, ge=1.0, description="Search radius in kilometers."),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(require_roles(Role.restaurant_owner, Role.admin)),
    db: Session = Depends(get_db),
):
    partners = get_available_partners_near_restaurant(
        db,
        restaurant_id=restaurant_id,
        radius_km=radius_km,
        limit=limit,
    )
    return partners


@router.post(
    "/assign",
    response_model=DeliveryPartnerRead,
    status_code=status.HTTP_201_CREATED,
    summary="Assign a delivery partner to an order",
)
def assign_partner(
    order_id: str = Body(..., embed=True),
    current_user: User = Depends(require_roles(Role.restaurant_owner, Role.admin)),
    db: Session = Depends(get_db),
):
    try:
        order, partner = assign_delivery_partner_to_order(db, order_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return partner


@router.post(
    "/order/{order_id}/location",
    response_model=OrderRead,
    summary="Update delivery partner GPS location and recalculate ETA",
)
def update_delivery_location(
    order_id: str,
    payload: dict = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        import uuid
        parsed_id = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order id.")

    required = {"partner_lat", "partner_lng"}
    if not required.issubset(payload):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="partner_lat and partner_lng are required.",
        )

    try:
        order = update_tracking(db, parsed_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    try:
        realtime_service.emit_location(
            order_id,
            {
                "lat": payload.get("partner_lat"),
                "lng": payload.get("partner_lng"),
                "heading": payload.get("heading"),
                "speed": payload.get("speed"),
                "updated_at": str(order.last_location_updated_at),
            },
        )
    except Exception:
        pass

    return order


@router.get(
    "/order/{order_id}/tracking",
    response_model=OrderRead,
    summary="Get tracking data for an order",
)
def get_order_tracking(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    try:
        import uuid
        parsed_id = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order id.")

    order = get_tracking(db, parsed_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    return order
