"""Socket.IO server for QuickBites real-time features.

Covers Phase 9.1:
- Socket server
- Socket authentication
- Room management
"""

import asyncio
from typing import Dict
import logging

import socketio
from fastapi import HTTPException
from app.core.config import settings

from app.core.security import decode_token
from app.crud.user import get_user
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

sio = socketio.AsyncServer(
    async_mode="asgi",
    # Let FastAPI's CORSMiddleware handle CORS headers globally to avoid
    # duplicate Access-Control-Allow-Origin values. Do not set cors_allowed_origins
    # here so the socketio server does not add its own CORS headers.
    # Align engineio's allowed origins with FastAPI CORSMiddleware settings.
    # Allow all origins in development to avoid websocket upgrade 403s caused
    # by subtle origin mismatches between localhost and 127.0.0.1.
    cors_allowed_origins="*" if (settings.DEBUG or not settings.cors_origins_list) else settings.cors_origins_list,
    logger=True,
    engineio_logger=True,
)

socket_app = socketio.ASGIApp(socketio_server=sio, socketio_path="/")

LIVE_SESSIONS: Dict[str, str] = {}


@sio.event
async def connect(sid: str, environ: dict, auth: dict | None = None) -> bool:
    logger.debug(f"[Socket.IO] Connect attempt - sid={sid}, auth={bool(auth)}, headers={environ.get('HTTP_ORIGIN', 'no origin')}")
    # Capture the main ASGI event loop so realtime helpers can schedule
    # coroutines from sync endpoints via run_coroutine_threadsafe.
    try:
        from app.services.realtime import set_main_event_loop as _set_loop
        _set_loop(asyncio.get_running_loop())
    except Exception:
        pass
    
    token = (auth or {}).get("token") if isinstance(auth, dict) else None
    if not token:
        # No token provided — reject the connection with 403
        logger.warning(f"[Socket.IO] No token provided for connection {sid}, auth content: {auth}")
        return False

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            logger.warning(f"[Socket.IO] Invalid token type for connection {sid}: {payload.get('type')}")
            return False
        user_id = payload.get("sub")
        logger.debug(f"[Socket.IO] Token decoded successfully for user {user_id}")
    except Exception as e:
        logger.error(f"[Socket.IO] Token decode failed for connection {sid}: {str(e)}, token: {token[:20]}...")
        return False

    db = SessionLocal()
    try:
        user = get_user(db, user_id)
        if not user or not user.is_active:
            logger.warning(f"[Socket.IO] User not found or inactive: {user_id}")
            return False
        logger.debug(f"[Socket.IO] User authenticated: {user.id} - {user.email}")
    except Exception as e:
        logger.error(f"[Socket.IO] User lookup failed for {user_id}: {str(e)}")
        return False
    finally:
        db.close()

    LIVE_SESSIONS[sid] = str(user.id)
    await sio.save_session(sid, {"user_id": str(user.id)})
    await sio.enter_room(sid, f"user:{user.id}")
    logger.info(f"[Socket.IO] Connection established: {sid} -> {user.id}")

    if user.role == "restaurant_owner":
        await sio.enter_room(sid, "role:restaurant_owner")
    elif user.role == "delivery_partner":
        await sio.enter_room(sid, "role:delivery_partner")
    elif user.role == "admin":
        await sio.enter_room(sid, "role:admin")
    
    return True


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
