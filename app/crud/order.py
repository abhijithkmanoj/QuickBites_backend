import uuid
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.db.models.order import Order, OrderItem
from app.db.models.payment import Payment
from app.db.models.cart import Cart
from app.schemas.order import OrderCreate
from app.services.checkout import calculate_checkout


def _parse_uuid(value: str | uuid.UUID) -> uuid.UUID | str:
    if isinstance(value, str):
        try:
            return uuid.UUID(value)
        except ValueError:
            return value
    return value


def get_order(db: Session, order_id: str | uuid.UUID) -> Optional[Order]:
    return (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.payment))
        .filter(Order.id == _parse_uuid(order_id))
        .first()
    )


def get_user_orders(
    db: Session,
    user_id: str | uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> List[Order]:
    return (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.payment))
        .filter(Order.customer_id == _parse_uuid(user_id))
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_restaurant_orders(
    db: Session,
    restaurant_id: str | uuid.UUID,
    skip: int = 0,
    limit: int = 50,
) -> List[Order]:
    return (
        db.query(Order)
        .options(joinedload(Order.items), joinedload(Order.payment))
        .filter(Order.restaurant_id == _parse_uuid(restaurant_id))
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_order_from_cart(
    db: Session,
    user_id: str | uuid.UUID,
    cart: Cart,
    order_in: OrderCreate,
) -> Order:
    """Create an order from the user's cart with full checkout calculation."""

    # Build price data from cart items
    items_price_data = [{"price": item.price, "quantity": item.quantity} for item in cart.items]

    # Calculate checkout amounts
    calc = calculate_checkout(items_price_data)

    # Build delivery address text
    delivery_text = order_in.delivery_address_text or ""

    # Create order
    order = Order(
        customer_id=_parse_uuid(user_id),
        restaurant_id=cart.restaurant_id,
        address_id=order_in.address_id,
        delivery_address_text=delivery_text,
        subtotal=calc["subtotal"],
        delivery_fee=calc["delivery_fee"],
        gst=calc["gst"],
        total_amount=calc["total_amount"],
        status="pending",
    )
    db.add(order)
    db.flush()

    # Create order items from cart items
    for cart_item in cart.items:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=cart_item.menu_item_id,
            name=cart_item.name,
            price=cart_item.price,
            quantity=cart_item.quantity,
        )
        db.add(order_item)

    # Create payment record (COD)
    payment = Payment(
        order_id=order.id,
        user_id=_parse_uuid(user_id),
        amount=calc["total_amount"],
        method="cod",
        status="pending",
    )
    db.add(payment)

    # Clear the cart
    for item in list(cart.items):
        db.delete(item)
    db.delete(cart)

    db.commit()
    db.refresh(order)
    return order


def update_order_status(
    db: Session,
    order: Order,
    new_status: str,
) -> Order:
    """Update order status."""
    order.status = new_status
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def accept_order(db: Session, order: Order) -> Order:
    """Accept a pending order."""
    if order.status != "pending":
        raise ValueError(f"Only pending orders can be accepted. Current status: '{order.status}'.")
    order.status = "accepted"
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def reject_order(db: Session, order: Order, reason: str | None = None) -> Order:
    """Reject a pending order. Marks as cancelled with an optional reason."""
    if order.status != "pending":
        raise ValueError(f"Only pending orders can be rejected. Current status: '{order.status}'.")
    order.status = "cancelled"
    if order.payment:
        order.payment.status = "cancelled"
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, order: Order) -> Order:
    """Cancel an order (only if pending or accepted)."""
    if order.status not in ("pending", "accepted"):
        raise ValueError(f"Cannot cancel order in '{order.status}' status.")
    order.status = "cancelled"
    if order.payment:
        order.payment.status = "cancelled"
    db.add(order)
    db.commit()
    db.refresh(order)
    return order
