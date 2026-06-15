import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

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


# ---------------------------------------------------------------------------
# Serve the pre-built frontend (React SPA) when running inside the unified
# Docker image. The frontend_dist directory exists only in the Docker image.
# ---------------------------------------------------------------------------
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend_dist"
if FRONTEND_DIST.is_dir():
    # Serve static assets (JS, CSS, images, favicon, etc.)
    app.mount(
        "/assets",
        StaticFiles(directory=str(FRONTEND_DIST / "assets")),
        name="frontend_assets",
    )

    # SPA fallback — all non-API, non-socket.io routes serve index.html
    # Support both GET and HEAD (Render's health checks may send HEAD)
    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_frontend(full_path: str):
        # Let the API and other mounts handle their own routes
        if (
            full_path.startswith("api/") or
            full_path.startswith("socket.io/") or
            full_path.startswith("docs") or
            full_path.startswith("redoc") or
            full_path.startswith("openapi") or
            full_path == "healthz" or
            full_path == "debug"
        ):
            raise HTTPException(status_code=404)
        index_path = FRONTEND_DIST / "index.html"
        if not index_path.is_file():
            raise HTTPException(status_code=404)
        return HTMLResponse(content=index_path.read_text(encoding="utf-8"))

    logger = logging.getLogger("app.frontend")
    logger.info("Frontend static files mounted from %s", FRONTEND_DIST)

# Wrap the FastAPI app with an ASGI wrapper that fixes CORS header duplication
# Do this after routes/mounts are set up so it runs at the ASGI send level
app = FixCorsASGI(app)