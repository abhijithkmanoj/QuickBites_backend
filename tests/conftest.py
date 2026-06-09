import os

import pytest
from fastapi.testclient import TestClient

DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    pytest.skip("DATABASE_URL (or TEST_DATABASE_URL) not provided — skipping backend tests.", allow_module_level=True)
if DATABASE_URL.lower().startswith("sqlite"):
    pytest.skip("SQLite is not supported for tests in this project. Set a PostgreSQL DATABASE_URL to run backend tests.", allow_module_level=True)

os.environ["DATABASE_URL"] = DATABASE_URL

from app.main import app
from app.api import deps
from app.db.base import Base
from app.db.session import engine, get_db, SessionLocal
from app.db.models.user import User
from app.db.models.refresh_token import RefreshToken
from app.db.models.menu_item import MenuItem
from app.db.models.delivery_partner import DeliveryPartner

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[deps.get_db] = override_get_db


@pytest.fixture(scope="session")
def client():
    return TestClient(app)
