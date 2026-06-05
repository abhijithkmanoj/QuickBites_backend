import logging

logger = logging.getLogger("app.redis")


def _get_redis_client():  # pragma: no cover - optional dependency
    logger.debug("Redis is disabled in this backend configuration.")
    return None


def ping() -> bool:
    return False
