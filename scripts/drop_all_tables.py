"""Drop all tables defined in SQLAlchemy metadata (use with caution).
"""
import os
import sys
import traceback

HERE = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from app.db.base import Base
    from app.db.session import engine
except Exception:
    print("Failed to import app metadata/engine")
    traceback.print_exc()
    raise

print("Dropping all tables defined in metadata...")
Base.metadata.drop_all(bind=engine)
print("Dropped all tables.")
