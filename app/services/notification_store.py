"""Lightweight in-memory notification store for development/testing.

This provides a simple thread-safe store to persist notifications per-user
for the duration of the process. It's intentionally simple so it can be
replaced by a DB-backed implementation later.
"""
from __future__ import annotations

import threading
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4


_lock = threading.Lock()
# user_id -> list[dict]
_store: Dict[str, List[dict]] = {}


def add_notification(user_id: str | int, payload: dict) -> str:
    nid = str(uuid4())
    entry = {
        "id": nid,
        "title": payload.get("title"),
        "body": payload.get("body"),
        "type": payload.get("type"),
        "order_id": payload.get("order_id"),
        "data": payload.get("data", {}),
        "read": False,
        "created_at": datetime.utcnow(),
    }
    key = str(user_id)
    with _lock:
        _store.setdefault(key, []).insert(0, entry)
    return nid


def get_notifications(user_id: str | int, skip: int = 0, limit: int = 20) -> (List[dict], int):
    key = str(user_id)
    with _lock:
        items = list(_store.get(key, []))
    total = len(items)
    return items[skip : skip + limit], total


def mark_read(user_id: str | int, notification_id: str) -> bool:
    key = str(user_id)
    with _lock:
        items = _store.get(key, [])
        for it in items:
            if it["id"] == notification_id:
                it["read"] = True
                return True
    return False


def mark_all_read(user_id: str | int) -> int:
    key = str(user_id)
    changed = 0
    with _lock:
        items = _store.get(key, [])
        for it in items:
            if not it.get("read"):
                it["read"] = True
                changed += 1
    return changed
