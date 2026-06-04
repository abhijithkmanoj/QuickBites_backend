"""Realtime Socket.IO event helpers for order lifecycle events."""

from __future__ import annotations

from typing import Any

from app.socket_server import sio


def emit(order_id: str, event: str, payload: dict[str, Any]) -> None:
    """Emit an order-related event to the matching order room."""
    sio.enter_room(order_id, f"order:{order_id}")
    sio.emit(event, payload, room=f"order:{order_id}")


def emit_status_update(order_id: str, order) -> None:
    emit(
        order_id,
        "order:status",
        {
            "order_id": order_id,
            "status": order.status,
            "updated_at": str(getattr(order, "updated_at", "")),
        },
    )


def emit_accepted(order_id: str, order) -> None:
    emit(
        order_id,
        "order:accepted",
        {
            "order_id": order_id,
            "message": "Order accepted by restaurant.",
            "restaurant_id": order.restaurant_id,
        },
    )


def emit_preparing(order_id: str, order) -> None:
    emit(
        order_id,
        "order:preparing",
        {
            "order_id": order_id,
            "message": "Restaurant is preparing your order.",
            "restaurant_id": order.restaurant_id,
        },
    )


def emit_picked_up(order_id: str, order) -> None:
    emit(
        order_id,
        "order:picked_up",
        {
            "order_id": order_id,
            "message": "Order has been picked up by delivery partner.",
            "delivery_partner_id": order.delivery_partner_id,
        },
    )


def emit_location(order_id: str, payload: dict[str, Any]) -> None:
    emit(
        order_id,
        "order:location",
        {
            "order_id": order_id,
            "lat": payload.get("lat"),
            "lng": payload.get("lng"),
            "heading": payload.get("heading"),
            "speed": payload.get("speed"),
            "updated_at": str(payload.get("updated_at") or ""),
        },
    )


def emit_delivered(order_id: str, order) -> None:
    emit(
        order_id,
        "order:delivered",
        {
            "order_id": order_id,
            "message": "Order delivered successfully.",
            "delivered_at": str(getattr(order, "delivered_at", "")),
        },
    )


def emit_new_assignment(order_id: str, partner_id: str) -> None:
    """Emit to delivery partner about new assignment."""
    sio.enter_room(partner_id, f"partner:{partner_id}")
    sio.emit("partner:new_assignment", {
        "order_id": order_id,
        "partner_id": partner_id,
    }, room=f"partner:{partner_id}")


def emit_owner_new_order(order_id: str, restaurant_id: str) -> None:
    """Emit to restaurant owner about new order."""
    sio.enter_room(restaurant_id, f"restaurant:{restaurant_id}")
    sio.emit("owner:new_order", {
        "order_id": order_id,
        "restaurant_id": restaurant_id,
    }, room=f"restaurant:{restaurant_id}")


def emit_order_assigned(order_id: str, partner_id: str) -> None:
    """Emit to delivery partner about new assignment."""
    emit_new_assignment(order_id, partner_id)


def emit_order_delivered(order_id: str) -> None:
    """Emit to customer that order is delivered."""
    sio.emit("order:delivered", {
        "order_id": order_id,
        "message": "Order delivered successfully.",
    }, room=f"order:{order_id}")