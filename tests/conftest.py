import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Use a temporary file-backed SQLite database for tests to ensure isolation
test_db_path = Path(__file__).resolve().parents[1] / f"test_{os.getpid()}.db"
TEST_DATABASE_URL = f"sqlite:///{test_db_path.as_posix()}"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

# Remove any existing test DB file from previous runs
if test_db_path.exists():
    try:
        test_db_path.unlink()
    except PermissionError:
        pass

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
