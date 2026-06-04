import logging
import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from app.core.config import settings

logger = logging.getLogger("app.security")

# In-memory sliding window rate limiter
# For production, replace with Redis-backed limiter
_rate_limit_store: dict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests: int = 100, window: int = 60):
        super().__init__(app)
        self.requests = requests
        self.window = window

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{request.url.path}"
        now = time.time()
        timestamps = _rate_limit_store[key]
        timestamps[:] = [t for t in timestamps if now - t < self.window]

        if len(timestamps) >= self.requests:
            logger.warning("Rate limit exceeded for %s on %s", client_ip, request.url.path)
            # Include CORS headers on the response so browsers receive them
            origin = request.headers.get("origin")
            allow_origins = settings.cors_origins_list
            headers = {}
            if allow_origins == ["*"]:
                headers["access-control-allow-origin"] = "*"
            elif origin and origin in allow_origins:
                headers["access-control-allow-origin"] = origin
            # Allow credentials if configured
            headers["access-control-allow-credentials"] = "true"
            headers["content-type"] = "application/json"
            return Response(content='{"detail":"Too many requests"}', status_code=429, media_type="application/json", headers=headers)

        timestamps.append(now)
        return await call_next(request)
