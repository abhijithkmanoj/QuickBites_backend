"""Create missing core tables by reflecting SQLAlchemy models and calling create_all.

This script imports the project's SQLAlchemy `Base` and model modules so
that all table metadata is registered, then calls `Base.metadata.create_all`
against the configured engine.

Usage (from repo root):
  $env:DATABASE_URL = '<postgres://...>'
  python backend/scripts/create_missing_core_tables.py
"""
import sys
import os
import traceback

# Ensure repo root is on sys.path so `import app` works when this script is
# executed from different working directories (e.g., backend or repo root).
_HERE = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", ".."))
# Add the backend directory to sys.path so `import app` resolves to backend/app
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

def main() -> int:
    try:
        # Importing these modules registers models with Base.metadata
        from app.db.base import Base
        import app.db.models  # noqa: F401
        from app.db.session import engine

        print("Creating tables from SQLAlchemy metadata...")
        Base.metadata.create_all(bind=engine)
        print("Done: metadata.create_all executed.")
        return 0
    except Exception as exc:
        print("Error creating tables:")
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
