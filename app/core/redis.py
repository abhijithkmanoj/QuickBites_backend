import logging
from typing import Optional

logger = logging.getLogger("app.redis")


def _get_redis_client():  # pragma: no cover - optional dependency
    try:
        import redis
    except ImportError:
        logger.warning("redis-py is not installed; Redis cache is disabled.")
        return None

    try:
        from app.core.config import settings
        return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    except Exception as exc:
        logger.warning("Redis client initialization failed: %s", exc)
        return None


def ping() -> bool:
    client = _get_redis_client()
    if client is None:
        return False
    try:
        return client.ping()
    except Exception:
        return False
