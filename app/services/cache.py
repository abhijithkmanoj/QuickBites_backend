from __future__ import annotations

import logging
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger("app.cache")


def _client():
    try:
        from app.core.redis import _get_redis_client
        return _get_redis_client()
    except Exception as exc:
        logger.debug("Redis cache unavailable: %s", exc)
        return None


def _key(name: str) -> str:
    return f"{settings.CACHE_PREFIX}{name}"


def get(key: str) -> Any | None:
    if not settings.USE_REDIS_CACHE:
        return None
    client = _client()
    if client is None:
        return None
    try:
        value = client.get(_key(key))
        if value is None:
            return None
        import json
        return json.loads(value)
    except Exception as exc:
        logger.debug("Cache get failed: %s", exc)
        return None


def set(key: str, value: Any, ttl_seconds: int = 300, *, nx: bool = False) -> bool:
    if not settings.USE_REDIS_CACHE:
        return False
    client = _client()
    if client is None:
        return False
    try:
        import json
        raw = json.dumps(value)
        method = client.set if not nx else client.setnx
        return bool(method(_key(key), raw, ex=ttl_seconds))
    except Exception as exc:
        logger.debug("Cache set failed: %s", exc)
        return False


def delete(key: str) -> None:
    if not settings.USE_REDIS_CACHE:
        return
    client = _client()
    if client is None:
        return
    try:
        client.delete(_key(key))
    except Exception as exc:
        logger.debug("Cache delete failed: %s", exc)


# Key constants
DELIVERY_LOCATION_KEY = "delivery:location:{order_id}"
RECOMMENDATION_KEY = "recommendations:{user_id}:v1"
SESSION_KEY = "session:{user_id}:{device}"
