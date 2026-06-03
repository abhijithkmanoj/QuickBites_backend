import html
import logging
import re
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

logger = logging.getLogger("app.security")

_XSS_PATTERN = re.compile(r"<.*?>", re.IGNORECASE | re.DOTALL)


def sanitize_text(value: str) -> str:
    if not isinstance(value, str):
        return value
    sanitized = html.escape(value)
    sanitized = _XSS_PATTERN.sub("", sanitized)
    return sanitized.strip()


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.method in {"POST", "PUT", "PATCH"}:
            try:
                body = await request.body()
                if body:
                    text = body.decode("utf-8", errors="ignore")
                    sanitized = sanitize_text(text)
                    if sanitized != text:
                        logger.warning("Sanitized request body for path=%s", request.url.path)
                        request._body = sanitized.encode("utf-8")
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("Sanitization step failed: %s", exc)
        return await call_next(request)
