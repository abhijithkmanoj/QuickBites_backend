"""Order auto-handler service.

When an order is placed, checks if all ordered menu items are in stock.
If all items have sufficient stock → auto-accept (stock decremented by accept_order).
If some items are out of stock → auto-reject with a reason listing which items.
"""

import logging
from typing import List

from sqlalchemy.orm import Session

from app.crud.menu_item import get_menu_item
from app.crud.order import accept_order, reject_order
from app.crud.restaurant import get_restaurant
from app.db.models.order import Order

logger = logging.getLogger(__name__)


def _get_out_of_stock_names(db: Session, order: Order) -> tuple[List[str], List[str]]:
    """Check stock for all items in the order.

    Returns:
        (out_of_stock_names, in_stock_names) — both lists.
    """
    out_of_stock: List[str] = []
    in_stock: List[str] = []

    for item in order.items:
        if item.menu_item_id is None:
            in_stock.append(item.name)
            continue
        menu_item = get_menu_item(db, item.menu_item_id)
        if menu_item is None or not menu_item.is_available:
            out_of_stock.append(item.name)
            continue
        # Check stock quantity
        if menu_item.stock_quantity is not None and menu_item.stock_quantity < item.quantity:
            out_of_stock.append(item.name)
        else:
            in_stock.append(item.name)

    return out_of_stock, in_stock


def _build_rejection_reason(out_of_stock: List[str], in_stock: List[str]) -> str:
    """Build a clear rejection reason in natural language, matching the user's requested style.

    Examples:
        - 'Paneer is currently out of stock, but Dal is available, try ordering after removing Paneer'
        - 'Paneer, Roti are currently out of stock, but Dal is available, try ordering after removing the unavailable items'
    """
    if not out_of_stock:
        return ""

    # Build the out-of-stock part
    if len(out_of_stock) == 1:
        oos_part = f"{out_of_stock[0]} is currently out of stock"
    else:
        oos_part = ", ".join(out_of_stock) + " are currently out of stock"

    # Build the in-stock part
    if in_stock:
        if len(in_stock) == 1:
            avail_part = f"but {in_stock[0]} is available"
        else:
            joined = ", ".join(in_stock)
            avail_part = f"but {joined} are available"

        # Build the action part
        if len(out_of_stock) == 1:
            action_part = f"try ordering after removing {out_of_stock[0]}"
        else:
            action_part = "try ordering after removing the unavailable items"

        return f"{oos_part}, {avail_part}, {action_part}"

    # All items are out of stock, nothing available
    if len(out_of_stock) == 1:
        return f"{out_of_stock[0]} is currently out of stock. Please remove it and try again."
    else:
        items_str = ", ".join(out_of_stock)
        return f"{items_str} are currently out of stock. Please remove them and try again."


def auto_handle_order(db: Session, order: Order) -> Order:
    """Check menu item stock and auto-accept or auto-reject the order.

    Only runs if the restaurant has auto_handle_orders enabled.
    When accepted, stock quantities are decremented automatically by accept_order.

    Args:
        db: Database session.
        order: The newly created order (must be in "pending" status).

    Returns:
        The updated Order with its new status (accepted, cancelled, or unchanged if skipped).
    """
    if order.status != "pending":
        logger.info(
            "Order %s is not pending (status=%s), skipping auto-handle.",
            order.id, order.status,
        )
        return order

    # Check if the restaurant has auto-handling enabled
    restaurant = get_restaurant(db, order.restaurant_id)
    if restaurant and not restaurant.auto_handle_orders:
        logger.info(
            "Order %s skipped — auto-handle is disabled for restaurant %s.",
            order.id, restaurant.id,
        )
        return order

    out_of_stock, in_stock = _get_out_of_stock_names(db, order)

    if not out_of_stock:
        # All items in stock — auto-accept (stock decremented inside accept_order)
        try:
            order = accept_order(db, order)
            logger.info("Order %s auto-accepted — stock decremented.", order.id)
        except ValueError as e:
            logger.warning("Failed to auto-accept order %s: %s", order.id, e)
        return order

    # Some items out of stock — auto-reject with a clear reason
    reason = _build_rejection_reason(out_of_stock, in_stock)

    try:
        order = reject_order(db, order, reason=reason)
        logger.info(
            "Order %s auto-rejected — out of stock: %s, in stock: %s",
            order.id, out_of_stock, in_stock,
        )
    except ValueError as e:
        logger.warning("Failed to auto-reject order %s: %s", order.id, e)

    return order
