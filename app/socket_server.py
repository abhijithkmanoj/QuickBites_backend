"""Socket.IO server for QuickBites real-time features.

Covers Phase 9.1:
- Socket server
- Socket authentication
- Room management
"""

from typing import Dict

import socketio
from fastapi import HTTPException

from app.core.security import decode_token
from app.crud.user import get_user
from app.db.session import SessionLocal

sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    logger=False,
    engineio_logger=False,
)

socket_app = socketio.ASGIApp(socketio_server=sio, socketio_path="")

LIVE_SESSIONS: Dict[str, str] = {}


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None = None) -> None:
    token = (auth or {}).get("token") if isinstance(auth, dict) else None
    if not token:
        await sio.disconnect(sid)
        raise HTTPException(status_code=401, detail="Missing auth token")

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise ValueError("Invalid token type")
        user_id = payload.get("sub")
    except Exception:
        await sio.disconnect(sid)
        raise HTTPException(status_code=401, detail="Invalid auth token")

    db = SessionLocal()
    try:
        user = get_user(db, user_id)
        if not user or not user.is_active:
            await sio.disconnect(sid)
            raise HTTPException(status_code=401, detail="Inactive user")
    finally:
        db.close()

    LIVE_SESSIONS[sid] = str(user.id)
    await sio.save_session(sid, {"user_id": str(user.id)})
    await sio.enter_room(sid, f"user:{user.id}")

    if user.role == "restaurant_owner":
        await sio.enter_room(sid, "role:restaurant_owner")
    elif user.role == "delivery_partner":
        await sio.enter_room(sid, "role:delivery_partner")
    elif user.role == "admin":
        await sio.enter_room(sid, "role:admin")


@sio.event
async def disconnect(sid: str) -> None:
    LIVE_SESSIONS.pop(sid, None)


@sio.event
async def join_order_room(sid: str, order_id: str) -> None:
    await sio.enter_room(sid, f"order:{order_id}")


@sio.event
async def leave_order_room(sid: str, order_id: str) -> None:
    await sio.leave_room(sid, f"order:{order_id}")


@sio.event
async def order_accepted(sid: str, data: dict) -> None:
    order_id = data.get("order_id")
    if order_id:
        await sio.emit("order:accepted", data, room=f"order:{order_id}")


@sio.event
async def order_preparing(sid: str, data: dict) -> None:
    order_id = data.get("order_id")
    if order_id:
        await sio.emit("order:preparing", data, room=f"order:{order_id}")


@sio.event
async def order_picked_up(sid: str, data: dict) -> None:
    order_id = data.get("order_id")
    if order_id:
        await sio.emit("order:picked_up", data, room=f"order:{order_id}")


@sio.event
async def order_location(sid: str, data: dict) -> None:
    order_id = data.get("order_id")
    if order_id:
        await sio.emit("order:location", data, room=f"order:{order_id}")


@sio.event
async def order_delivered(sid: str, data: dict) -> None:
    order_id = data.get("order_id")
    if order_id:
        await sio.emit("order:delivered", data, room=f"order:{order_id}")
