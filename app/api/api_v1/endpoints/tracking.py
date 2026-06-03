from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_active_user
from app.crud.tracking import update_tracking, get_tracking
from app.db.models.user import User
from app.schemas.order import OrderRead

router = APIRouter()


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
