from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("app.cache")

CACHE_PREFIX = "quickbites:"


def _key(name: str) -> str:
    return f"{CACHE_PREFIX}{name}"


def get(key: str) -> Any | None:
    return None


def set(key: str, value: Any, ttl_seconds: int = 300, *, nx: bool = False) -> bool:
    return False


def delete(key: str) -> None:
    return


# Key constants
DELIVERY_LOCATION_KEY = "delivery:location:{order_id}"
RECOMMENDATION_KEY = "recommendations:{user_id}:v1"
SESSION_KEY = "session:{user_id}:{device}"
