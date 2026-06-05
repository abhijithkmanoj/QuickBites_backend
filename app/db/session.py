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

# Ensure Psycopg v3 driver is explicitly used (not psycopg2)
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
elif not database_url.startswith("postgresql+psycopg://"):
    logger.warning("Database URL does not use Psycopg v3 driver. Ensure compatible driver is installed.")

logger.info("Using database driver: psycopg (v3)")

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    future=True,
    connect_args={
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
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
