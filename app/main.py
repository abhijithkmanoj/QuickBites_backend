from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_v1.api import router as api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.socket_server import socket_app
from fastapi.middleware.cors import CORSMiddleware as StarletteCORSMiddleware

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs" if settings.ENABLE_DOCS else None,
    redoc_url="/redoc" if settings.ENABLE_DOCS else None,
)

# Fix CORS headers emitted by some mounted apps (socket.io) by running a
# final dedupe middleware after responses are generated.
from app.core.middleware import FixCorsHeadersMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)

app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    RateLimitMiddleware,
    requests=settings.RATE_LIMIT_REQUESTS,
    window=settings.RATE_LIMIT_WINDOW_SECONDS,
)

# Register the FixCorsHeadersMiddleware last so it can clean headers after
# CORSMiddleware and any mounted apps have added their headers.
app.add_middleware(FixCorsHeadersMiddleware)

register_exception_handlers(app)

app.include_router(
    api_router,
    prefix=settings.API_V1_STR,
)

from app.core.middleware import FixCorsASGI

# Wrap the socketio ASGI app so its responses get header normalization too
# Ensure the mounted socket_app has permissive CORS in development so the
# websocket upgrade isn't rejected before it reaches the Socket.IO server.
socket_app = StarletteCORSMiddleware(
    socket_app,
    allow_origins=["*"] if settings.DEBUG else settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
socket_app = FixCorsASGI(socket_app)
app.mount("/socket.io", socket_app)

# Wrap the FastAPI app with an ASGI wrapper that fixes CORS header duplication
@app.get("/healthz", include_in_schema=False)
def health_probe():
    return {"status": "ok"}


@app.get("/debug")
def debug():
    return {
        "debug": settings.DEBUG,
        "environment": settings.ENVIRONMENT,
        "enable_docs": settings.ENABLE_DOCS,
        "docs_url": app.docs_url,
        "openapi_url": app.openapi_url,
    }

# Wrap the FastAPI app with an ASGI wrapper that fixes CORS header duplication
# Do this after routes/mounts are set up so it runs at the ASGI send level
app = FixCorsASGI(app)