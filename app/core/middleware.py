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
        # Deduplicate CORS-related headers to avoid multiple comma-separated values
        for h in ("access-control-allow-origin", "access-control-allow-credentials"):
            val = response.headers.get(h)
            if val and "," in val:
                parts = [p.strip() for p in val.split(",") if p.strip()]
                # preserve order and keep unique
                seen = set()
                uniq = []
                for p in parts:
                    if p not in seen:
                        seen.add(p)
                        uniq.append(p)
                # set to a single value if possible
                response.headers[h] = uniq[0] if len(uniq) == 1 else ", ".join(uniq)
        return response


class FixCorsHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        # Normalize and dedupe CORS headers emitted by multiple components
        for h in ("access-control-allow-origin", "access-control-allow-credentials"):
            val = response.headers.get(h)
            if val and "," in val:
                parts = [p.strip() for p in val.split(",") if p.strip()]
                seen = set()
                uniq = []
                for p in parts:
                    if p not in seen:
                        seen.add(p)
                        uniq.append(p)
                response.headers[h] = uniq[0] if len(uniq) == 1 else ", ".join(uniq)
        return response


class FixCorsASGI:
    """ASGI wrapper that normalizes/deduplicates CORS headers on http responses.

    This operates at the ASGI send level so it runs after all middleware and
    response processing and guarantees the final headers are adjusted before
    being sent to the client.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(event):
            if event.get("type") == "http.response.start":
                headers = event.setdefault("headers", [])
                # Debug: log raw headers for socket.io to diagnose duplication
                try:
                    path = scope.get("path", "")
                except Exception:
                    path = ""
                if path.startswith("/socket.io"):
                    logger = logging.getLogger("app.middleware")
                    logger.debug("FixCorsASGI raw headers for %s: %r", path, headers)
                # headers is a list of (name: bytes, value: bytes)
                # collect and dedupe values for target headers
                target_names = {"access-control-allow-origin", "access-control-allow-credentials"}
                hdr_map: dict[str, list[str]] = {}
                others: list[tuple[bytes, bytes]] = []
                for name, value in headers:
                    try:
                        name_str = name.decode("latin-1").lower()
                    except Exception:
                        name_str = str(name).lower()
                    if name_str in target_names:
                        # split comma-separated values (some libs may combine headers)
                        raw_val = value.decode("latin-1")
                        for part in [p.strip() for p in raw_val.split(",") if p.strip()]:
                            hdr_map.setdefault(name_str, []).append(part)
                    else:
                        others.append((name, value))

                new_headers = others
                for t in ("access-control-allow-origin", "access-control-allow-credentials"):
                    vals = hdr_map.get(t, [])
                    if vals:
                        # dedupe while preserving order
                        seen = set()
                        uniq = []
                        for v in vals:
                            if v not in seen:
                                seen.add(v)
                                uniq.append(v)
                        final = uniq[0] if len(uniq) == 1 else ", ".join(uniq)
                        new_headers.append((t.encode("latin-1"), final.encode("latin-1")))

                event["headers"] = new_headers

            await send(event)

        await self.app(scope, receive, send_wrapper)
