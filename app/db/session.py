import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

logger = logging.getLogger(__name__)

if not settings.DATABASE_URL or not settings.DATABASE_URL.strip():
    raise RuntimeError(
        "DATABASE_URL must be provided by the environment before starting the app. "
        "On Railway, configure the PostgreSQL plugin and ensure DATABASE_URL is injected. "
        "Supported alternate env vars: POSTGRES_URL, POSTGRESQL_URL, RAILWAY_DATABASE_URL."
    )

logger.info("Database connection target: %s", settings.database_url_info)

if settings.DATABASE_URL.lower().startswith("sqlite"):
    raise RuntimeError(
        "SQLite is not supported. Use a hosted PostgreSQL DATABASE_URL instead."
    )

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
