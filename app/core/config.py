import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine.url import make_url

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "QuickBites Backend"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    ENABLE_DOCS: bool = True
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: Optional[str] = None

    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"
    REFRESH_TOKEN_COOKIE_MAX_AGE: int = 604800
    JWT_ALGORITHM: str = "HS256"

    # Must be provided from .env
    CORS_ORIGINS: str = Field(...)

    CACHE_PREFIX: str = "quickbites:"

    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_USE_TLS: bool = True

    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    FIREBASE_SENDER_ID: Optional[str] = None

    # Stripe / Payments
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLISHABLE_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    PAYMENTS_ENABLED: bool = False

    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    @field_validator("DEBUG", mode="before")
    @classmethod
    def coerce_debug(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return True
        return str(value).strip().lower() not in (
            "false",
            "0",
            "no",
            "off",
            "release",
        )

    @field_validator("ENABLE_DOCS", mode="before")
    @classmethod
    def coerce_enable_docs(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return True
        return str(value).strip().lower() not in (
            "false",
            "0",
            "no",
            "off",
        )

    @field_validator("CORS_ORIGINS")
    @classmethod
    def validate_cors_origins(cls, value):
        if not value or not value.strip():
            raise ValueError(
                "CORS_ORIGINS must be provided in .env or environment variables"
            )
        return value.strip()

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, value):
        if isinstance(value, str):
            value = value.strip()

        if not value:
            for alias in (
                "DATABASE_URL",
                "POSTGRES_URL",
                "POSTGRESQL_URL",
                "RAILWAY_DATABASE_URL",
                "PG_URL",
                "PG_URI",
            ):
                value = os.environ.get(alias)
                if isinstance(value, str):
                    value = value.strip()
                if value:
                    break

        if not value:
            return None

        try:
            parsed = make_url(value)
        except Exception as exc:
            raise ValueError(
                f"DATABASE_URL is invalid: {exc}. "
                f"Provide a valid SQLAlchemy URL like "
                f"postgresql://user:pass@host:port/dbname"
            ) from exc

        if (
            str(parsed.username).lower() == "username"
            or str(parsed.password).lower() == "password"
            or str(parsed.host).lower() == "host"
            or str(parsed.database).lower() == "database"
        ):
            raise ValueError(
                "DATABASE_URL appears to contain placeholder values. "
                "Replace DATABASE_URL in backend/.env or environment variables "
                "with your hosted Neon Postgres connection string."
            )

        return value

    @property
    def cors_origins_list(self) -> List[str]:
        origins = []
        for origin in self.CORS_ORIGINS.split(","):
            o = origin.strip()
            if not o:
                continue
            # Normalize by removing a trailing slash, e.g. http://localhost:5173/
            if o != "*":
                o = o.rstrip("/")
            origins.append(o)
        return origins

    @property
    def database_url_info(self) -> str:
        if not self.DATABASE_URL:
            return "DATABASE_URL is not configured"

        parsed = make_url(self.DATABASE_URL)

        host = parsed.host or "unknown-host"
        database = parsed.database or "unknown-db"
        port = f":{parsed.port}" if parsed.port else ""

        return f"{host}{port}/{database}"

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()