import logging
import time
from collections import defaultdict
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response

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
            return Response(content='{"detail":"Too many requests"}', status_code=429, media_type="application/json")

        timestamps.append(now)
        return await call_next(request)
