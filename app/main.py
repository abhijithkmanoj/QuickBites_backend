from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api_v1.api import router as api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.core.rate_limit import RateLimitMiddleware
from app.socket_server import socket_app

setup_logging()

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

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
app.add_middleware(RateLimitMiddleware, requests=settings.RATE_LIMIT_REQUESTS, window=settings.RATE_LIMIT_WINDOW_SECONDS)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_STR)
app.mount("/socket.io", socket_app)


@app.get("/healthz", include_in_schema=False)
def health_probe():
    return {"status": "ok"}
