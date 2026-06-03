import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from app.core.monitoring import increment_request

logger = logging.getLogger("app.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response: Response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(
            "%s %s %s %.2fms",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
        )
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        increment_request(request.url.path, response.status_code)
        return response
