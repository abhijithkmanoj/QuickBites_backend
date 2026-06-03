"""Production-only configuration helpers."""

import os


def get_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "")
    if not raw:
        return ["*"]
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def is_production() -> bool:
    return os.getenv("ENVIRONMENT", "development").lower() == "production"
