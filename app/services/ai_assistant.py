"""AI Assistant service.

Provides food search, order tracking, and complaint handling.
This is a rule-based assistant that can be upgraded to an LLM later.
"""
from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.models.order import Order
from app.db.models.restaurant import Restaurant
from app.db.models.menu_item import MenuItem


INTENT_PATTERNS = {
    "food_search": re.compile(r"\b(search|find|show|browse|looking for|recommend)\b", re.IGNORECASE),
    "order_tracking": re.compile(r"\b(track|status|where is|tracking)\b.*\b(order|#)?\s*([A-Za-z0-9-]+)?\b", re.IGNORECASE),
    "complaint": re.compile(r"\b(complain|issue|problem|bad|wrong|not received|late)\b", re.IGNORECASE),
}


def _detect_intent(message: str) -> str:
    if INTENT_PATTERNS["complaint"].search(message):
        return "complaint"
    if INTENT_PATTERNS["order_tracking"].search(message):
        return "order_tracking"
    if INTENT_PATTERNS["food_search"].search(message):
        return "food_search"
    return "unknown"


def _search_food(db: Session, query: str, limit: int = 10) -> list[dict[str, Any]]:
    pattern = f"%{query}%"
    items = (
        db.query(MenuItem)
        .join(Restaurant, MenuItem.restaurant_id == Restaurant.id)
        .filter(MenuItem.name.ilike(pattern) | MenuItem.description.ilike(pattern) | Restaurant.cuisine.ilike(pattern))
        .limit(limit)
        .all()
    )
    return [
        {
            "id": str(item.id),
            "name": item.name,
            "price": item.price,
            "restaurant_name": item.restaurant.name if item.restaurant else None,
            "category": item.category,
        }
        for item in items
    ]


def _get_order_status(db: Session, order_id: str) -> dict[str, Any] | None:
    try:
        parsed = UUID(order_id)
    except ValueError:
        return None
    order = db.query(Order).filter(Order.id == parsed).first()
    if not order:
        return None
    return {
        "order_id": str(order.id),
        "status": order.status,
        "total_amount": order.total_amount,
        "delivery_address_text": order.delivery_address_text,
        "created_at": order.created_at.isoformat() if order.created_at else None,
    }


def _get_user_recent_orders(db: Session, user_id: str | UUID, limit: int = 5) -> list[dict[str, Any]]:
    parsed = user_id if isinstance(user_id, UUID) else UUID(str(user_id))
    orders = (
        db.query(Order)
        .filter(Order.customer_id == parsed)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "order_id": str(o.id),
            "status": o.status,
            "total_amount": o.total_amount,
            "created_at": o.created_at.isoformat() if o.created_at else None,
        }
        for o in orders
    ]


def _extract_order_id(message: str) -> str | None:
    match = re.search(r"\b([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\b", message)
    return match.group(1) if match else None


def process_chat(db: Session, user_id: str | None, message: str) -> dict[str, Any]:
    intent = _detect_intent(message)

    if intent == "food_search":
        results = _search_food(db, message)
        if results:
            return {
                "intent": "food_search",
                "reply": f"I found {len(results)} food options for you.",
                "data": results,
            }
        return {
            "intent": "food_search",
            "reply": "I couldn't find any matching food items. Try a different keyword.",
            "data": [],
        }

    if intent == "order_tracking":
        order_id = _extract_order_id(message)
        if order_id:
            order = _get_order_status(db, order_id)
            if order:
                return {
                    "intent": "order_tracking",
                    "reply": f"Order {order['order_id']} is currently {order['status']}.",
                    "data": order,
                }
            return {
                "intent": "order_tracking",
                "reply": f"Order {order_id} not found. Please check the order ID.",
                "data": None,
            }
        if user_id:
            orders = _get_user_recent_orders(db, user_id)
            if orders:
                return {
                    "intent": "order_tracking",
                    "reply": "Here are your recent orders:",
                    "data": orders,
                }
            return {
                "intent": "order_tracking",
                "reply": "You don't have any recent orders.",
                "data": [],
            }
        return {
            "intent": "order_tracking",
            "reply": "Please provide your order ID or log in to see your orders.",
            "data": None,
        }

    if intent == "complaint":
        return {
            "intent": "complaint",
            "reply": "I'm sorry to hear that. I've noted your complaint. Our support team will reach out shortly.",
            "data": {"status": "escalated"},
        }

    return {
        "intent": "unknown",
        "reply": "I can help with food search, order tracking, and complaints. What would you like to do?",
        "data": None,
    }
