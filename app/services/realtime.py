"""Realtime Socket.IO event helpers for order lifecycle events."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Iterable

from app.socket_server import sio

logger = logging.getLogger(__name__)

# Holds a reference to the main ASGI event loop so sync endpoints (which run in
# a threadpool) can schedule socketio coroutines via run_coroutine_threadsafe.
_main_event_loop: asyncio.AbstractEventLoop | None = None


def set_main_event_loop(loop: asyncio.AbstractEventLoop) -> None:
    """Store a reference to the main ASGI event loop.

    Called from the socket server's connect handler (which runs on the main
    event loop) so that _fire_and_forget can use run_coroutine_threadsafe.
    """
    global _main_event_loop
    _main_event_loop = loop


def _fire_and_forget(coro):
    """Schedule an async coroutine on the main ASGI event loop.

    Since sio is an AsyncServer, all its methods are coroutines.
    These helpers are called from sync FastAPI endpoints (run in a threadpool),
    so we must schedule coroutines on the main event loop via
    run_coroutine_threadsafe rather than trying get_event_loop() which will
    fail from a threadpool thread.
    """
    try:
        if _main_event_loop is not None and _main_event_loop.is_running():
            asyncio.run_coroutine_threadsafe(coro, _main_event_loop)
            return
        # Fallback: try to schedule on whatever loop is available
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(coro)
        else:
            asyncio.run(coro)
    except RuntimeError:
        logger.exception("No event loop available for socket emit")
    except Exception:
        logger.exception("Socket emit failed")


def emit(order_id: str, event: str, payload: dict[str, Any]) -> None:
    """Emit an order-related event to the matching order room."""
    room_name = order_id if str(order_id).startswith('order:') else f'order:{order_id}'
    _fire_and_forget(sio.emit(event, payload, room=room_name))


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


def _enter_room(sid: str, room: str) -> None:
    """Schedule enter_room on the async server.
    Note: sid is a socket session ID, not a user/partner database ID.
    """
    _fire_and_forget(sio.enter_room(sid, room))


def emit_new_assignment(order_id: str, partner_id: str) -> None:
    """Emit to delivery partner about new assignment."""
    _enter_room(partner_id, f"partner:{partner_id}")
    _fire_and_forget(sio.emit("partner:new_assignment", {
        "order_id": order_id,
        "partner_id": partner_id,
    }, room=f"partner:{partner_id}"))


def emit_owner_new_order(order_id: str, restaurant_id: str) -> None:
    """Emit to restaurant owner about new order."""
    _enter_room(restaurant_id, f"restaurant:{restaurant_id}")
    _fire_and_forget(sio.emit("owner:new_order", {
        "order_id": order_id,
        "restaurant_id": restaurant_id,
    }, room=f"restaurant:{restaurant_id}"))


def emit_order_assigned(order_id: str, partner_id: str) -> None:
    """Emit to delivery partner about new assignment."""
    emit_new_assignment(order_id, partner_id)


def emit_order_delivered(order_id: str) -> None:
    """Emit to customer that order is delivered."""
    _fire_and_forget(sio.emit("order:delivered", {
        "order_id": order_id,
        "message": "Order delivered successfully.",
    }, room=f"order:{order_id}"))


def emit_notification_to_users(user_ids: Iterable[str], payload: dict[str, Any]) -> None:
    """Emit a generic notification payload to each user's socket room.

    Payload example: { type, title, body, order_id, timestamp }
    """
    for uid in user_ids:
        _fire_and_forget(sio.emit("notification", payload, room=f"user:{uid}"))