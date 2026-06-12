import uuid
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.db.models.order import Order, OrderItem
from app.db.models.payment import Payment
from app.db.models.cart import Cart
from app.schemas.order import OrderCreate
from app.services.checkout import calculate_checkout
from app.services import promotions as promotions_service


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

    # Apply promotions if any
    total_discount_cents = 0
    applied_promotion_id = None
    if getattr(order_in, 'promo_codes', None):
        # validate each code
        valid_promos = []
        for code in order_in.promo_codes:
            res = promotions_service.validate_promo_for_user(db, user_id, code, int(round(calc['total_amount'] * 100)))
            if res.get('valid'):
                # fetch promotion to check stackability
                promo = promotions_service.get_promotion_by_code(db, code)
                if promo:
                    valid_promos.append({'promo': promo, 'discount_cents': int(res.get('discount_cents', 0))})

        if valid_promos:
            # If any non-stackable promos exist, pick the single highest discount among them
            non_stackables = [p for p in valid_promos if not p['promo'].is_stackable]
            if non_stackables:
                best = max(non_stackables, key=lambda x: x['discount_cents'])
                total_discount_cents = best['discount_cents']
                applied_promotion_id = best['promo'].id
            else:
                # sum stackable promos
                total_discount_cents = sum(p['discount_cents'] for p in valid_promos)
                applied_promotion_id = valid_promos[0]['promo'].id

    discount_amount = round(total_discount_cents / 100.0, 2)

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
        total_amount=max(0.0, round(calc["total_amount"] - discount_amount, 2)),
        discount_amount=discount_amount,
        applied_promotion_id=applied_promotion_id,
        status="pending",
    )
    db.add(order)
    db.flush()

    # Create order items from cart items, deduplicating by menu_item_id.
    # This handles any duplicate cart items that may exist in the database
    # (e.g., from before the add_item_to_cart dedup fix was deployed).
    seen: dict[str, dict] = {}
    for cart_item in cart.items:
        key = str(cart_item.menu_item_id) if cart_item.menu_item_id else cart_item.id
        if key in seen:
            # Duplicate menu_item_id — merge quantity into the first occurrence
            seen[key]["quantity"] += cart_item.quantity
        else:
            seen[key] = {
                "menu_item_id": cart_item.menu_item_id,
                "name": cart_item.name,
                "price": cart_item.price,
                "quantity": cart_item.quantity,
            }
    for entry in seen.values():
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=entry["menu_item_id"],
            name=entry["name"],
            price=entry["price"],
            quantity=entry["quantity"],
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

    # Record promotion usage(s)
    try:
        if total_discount_cents and getattr(order_in, 'promo_codes', None):
            # record only for codes that validated
            for code in order_in.promo_codes:
                res = promotions_service.validate_promo_for_user(db, user_id, code, int(round(calc['total_amount'] * 100)))
                if res.get('valid'):
                    try:
                        promotions_service.record_promotion_usage(db, res.get('promo_id'), user_id, order.id, int(res.get('discount_cents', 0)))
                    except Exception:
                        pass
    except Exception:
        pass
    return order


def _restore_stock(db: Session, order: Order) -> None:
    """Restore stock quantities and re-enable menu items when an accepted order is cancelled."""
    from app.crud.menu_item import get_menu_item

    for item in order.items:
        if item.menu_item_id is None:
            continue
        menu_item = get_menu_item(db, item.menu_item_id)
        if menu_item is None or menu_item.stock_quantity is None:
            continue  # Skip items with unlimited stock or that no longer exist
        menu_item.stock_quantity += item.quantity
        if not menu_item.is_available and menu_item.stock_quantity > 0:
            menu_item.is_available = True
        db.add(menu_item)


def update_order_status(
    db: Session,
    order: Order,
    new_status: str,
) -> Order:
    """Update order status. Restores stock if transitioning from accepted to cancelled."""
    was_accepted = order.status == "accepted"
    order.status = new_status
    db.add(order)

    if was_accepted and new_status == "cancelled":
        _restore_stock(db, order)

    db.commit()
    db.refresh(order)
    return order


def accept_order(db: Session, order: Order) -> Order:
    """Accept a pending order and decrement stock for all items."""
    if order.status != "pending":
        raise ValueError(f"Only pending orders can be accepted. Current status: '{order.status}'.")
    order.status = "accepted"
    db.add(order)

    # Decrement stock for each item in the order
    from app.crud.menu_item import get_menu_item
    for item in order.items:
        if item.menu_item_id is None:
            continue
        menu_item = get_menu_item(db, item.menu_item_id)
        if menu_item is None or menu_item.stock_quantity is None:
            continue  # Skip items with unlimited stock
        menu_item.stock_quantity -= item.quantity
        if menu_item.stock_quantity <= 0:
            menu_item.stock_quantity = 0
            menu_item.is_available = False
        db.add(menu_item)

    db.commit()
    db.refresh(order)
    return order


def reject_order(db: Session, order: Order, reason: str | None = None) -> Order:
    """Reject a pending order. Marks as cancelled with an optional reason."""
    if order.status != "pending":
        raise ValueError(f"Only pending orders can be rejected. Current status: '{order.status}'.")
    order.status = "cancelled"
    order.rejection_reason = reason
    if order.payment:
        order.payment.status = "cancelled"
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, order: Order) -> Order:
    """Cancel an order (only if pending or accepted). Restores stock if order was accepted."""
    if order.status not in ("pending", "accepted"):
        raise ValueError(f"Cannot cancel order in '{order.status}' status.")
    was_accepted = order.status == "accepted"
    order.status = "cancelled"
    if order.payment:
        order.payment.status = "cancelled"
    db.add(order)

    if was_accepted:
        _restore_stock(db, order)

    db.commit()
    db.refresh(order)
    return order
