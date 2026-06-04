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
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = Field(..., min_length=1)
    SECRET_KEY: str = "change-me"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"
    REFRESH_TOKEN_COOKIE_MAX_AGE: int = 604800
    JWT_ALGORITHM: str = "HS256"
    
    CORS_ORIGINS: str = "*"

    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_PREFIX: str = "quickbites:"
    USE_REDIS_CACHE: bool = False

    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_USE_TLS: bool = True

    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    FIREBASE_SENDER_ID: Optional[str] = None

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
            "false", "0", "no", "off", "release"
        )

    @field_validator("USE_REDIS_CACHE", mode="before")
    @classmethod
    def coerce_use_redis(cls, value):
        if isinstance(value, bool):
            return value
        if value is None:
            return False
        return str(value).strip().lower() in (
            "true", "1", "yes", "on"
        )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, value):
        if isinstance(value, str):
            value = value.strip()
        if not value:
            raise ValueError(
                "DATABASE_URL is required and must be set in Railway env vars or backend/.env. "
                "Example: postgresql://user:pass@host:port/dbname"
            )
        try:
            make_url(value)
        except Exception as exc:
            raise ValueError(
                f"DATABASE_URL is invalid: {exc}. Provide a valid SQLAlchemy URL like postgresql://user:pass@host:port/dbname"
            ) from exc
        return value

    @property
    def cors_origins_list(self) -> List[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        import json
        if self.CORS_ORIGINS.startswith('[') and self.CORS_ORIGINS.endswith(']'):
            try:
                return json.loads(self.CORS_ORIGINS)
            except Exception:
                pass
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()