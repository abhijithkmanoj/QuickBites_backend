from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_active_user
from app.crud.cart import get_cart_by_user
from app.crud.order import (
    accept_order,
    cancel_order,
    create_order_from_cart,
    get_order,
    get_user_orders,
    reject_order,
    update_order_status,
)
from app.crud.address import get_address
from app.crud.restaurant import get_restaurant
from app.db.models.user import User
from app.schemas.order import OrderCreate, OrderRead, OrderReject, OrderStatusUpdate
from app.services import realtime as realtime_service
from app.services.firebase_notifications import FirebaseNotificationService
from app.services.notifications import EmailService

router = APIRouter()


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED, summary="Place a new order")
def place_order(
    order_in: OrderCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Create an order from the current user's cart with COD payment."""
    cart = get_cart_by_user(db, current_user.id)
    if not cart or not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty.")

    # Validate address if provided
    if order_in.address_id:
        address = get_address(db, order_in.address_id)
        if not address:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found.")
        if str(address.user_id) != str(current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Address does not belong to user.")
        # Build delivery text from address
        parts = [address.street, address.city, address.state, address.postal_code]
        if address.landmark:
            parts.append(address.landmark)
        order_in.delivery_address_text = ", ".join(parts)

    order = create_order_from_cart(db, current_user.id, cart, order_in)
    try:
        FirebaseNotificationService.send_order_notification(
            order_id=str(order.id),
            user_ids=[str(order.restaurant.owner_id)] if order.restaurant and order.restaurant.owner_id else [],
            title="New Order Received",
            body=f"Order #{order.id} has been placed.",
        )
        EmailService.send_order_confirmation(current_user.email, str(order.id), order.total_amount)
    except Exception:
        pass
    return order


@router.get("", response_model=List[OrderRead], summary="List user's orders")
def list_orders(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    return get_user_orders(db, current_user.id, skip=skip, limit=limit)


@router.get("/{order_id}", response_model=OrderRead, summary="Get order details")
def read_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    # Allow customer or restaurant owner to view
    if str(order.customer_id) != str(current_user.id):
        if current_user.role in ("restaurant_owner", "admin"):
            # Check if user owns the restaurant for this order
            restaurant = get_restaurant(db, order.restaurant_id)
            if not restaurant or (current_user.role == "restaurant_owner" and str(restaurant.owner_id) != str(current_user.id)):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")

    return order


VALID_TRANSITIONS = {
    "pending": ["accepted", "cancelled"],
    "accepted": ["preparing", "assigned", "cancelled"],
    "preparing": ["ready_for_pickup", "assigned"],
    "assigned": ["picked_up"],
    "ready_for_pickup": ["picked_up", "assigned"],
    "picked_up": ["delivered"],
}


@router.put("/{order_id}/status", response_model=OrderRead, summary="Update order status (restaurant owner)")
def update_status(
    order_id: str,
    status_in: OrderStatusUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update order status. Restaurant owners can move orders through the workflow."""
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    # Only restaurant owner or admin can update status
    if current_user.role not in ("restaurant_owner", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only restaurant owners can update order status.")

    if current_user.role == "restaurant_owner":
        restaurant = get_restaurant(db, order.restaurant_id)
        if not restaurant or str(restaurant.owner_id) != str(current_user.id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions for this order.")

    # Validate status transition
    allowed = VALID_TRANSITIONS.get(order.status, [])
    if status_in.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{order.status}' to '{status_in.status}'. Allowed: {allowed}",
        )

    try:
        order = update_order_status(db, order, status_in.status)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    try:
        realtime_service.emit_status_update(order_id, order)
        if status_in.status == "preparing":
            realtime_service.emit_preparing(order_id, order)
        elif status_in.status == "picked_up":
            realtime_service.emit_picked_up(order_id, order)
        elif status_in.status == "delivered":
            realtime_service.emit_delivered(order_id, order)

        user_ids = [str(order.customer_id)]
        if order.restaurant and order.restaurant.owner_id:
            user_ids.append(str(order.restaurant.owner_id))
        if order.delivery_partner_id:
            user_ids.append(str(order.delivery_partner_id))

        FirebaseNotificationService.send_order_notification(
            order_id=order_id,
            user_ids=user_ids,
            title=f"Order Updated",
            body=f"Order #{order_id} is now {status_in.status}.",
        )
    except Exception:
        pass

    return order


@router.put("/{order_id}/cancel", response_model=OrderRead, summary="Cancel an order")
def cancel_existing_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    if str(order.customer_id) != str(current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
    try:
        order = cancel_order(db, order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return order


def _owner_or_admin_check(order, current_user, db):
    """Check if current user is the restaurant owner or admin for this order."""
    if current_user.role not in ("restaurant_owner", "admin"):
        return False
    if current_user.role == "admin":
        return True
    restaurant = get_restaurant(db, order.restaurant_id)
    return bool(restaurant and str(restaurant.owner_id) == str(current_user.id))


@router.put("/{order_id}/accept", response_model=OrderRead, summary="Accept a pending order")
def accept_existing_order(
    order_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Accept a pending order. Restaurant owner only."""
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    if not _owner_or_admin_check(order, current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
    try:
        order = accept_order(db, order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    try:
        realtime_service.emit_accepted(str(order.id), order)
    except Exception:
        pass
    return order


@router.put("/{order_id}/reject", response_model=OrderRead, summary="Reject a pending order")
def reject_existing_order(
    order_id: str,
    reject_in: OrderReject,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Reject a pending order with an optional reason. Restaurant owner only."""
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")
    if not _owner_or_admin_check(order, current_user, db):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions.")
    try:
        order = reject_order(db, order, reason=reject_in.reason)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return order
