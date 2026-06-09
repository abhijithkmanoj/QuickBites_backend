"""Add missing columns to existing tables based on SQLAlchemy metadata.

This script inspects the DB and for each table present will add any columns
declared in the SQLAlchemy models but missing in the actual DB schema.
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
    from sqlalchemy import inspect
    from app.db.base import Base
    import app.db.models  # register models
    from app.db.session import engine
except Exception:
    print("Failed to import app models; ensure DATABASE_URL is set and backend package is importable.")
    traceback.print_exc()
    sys.exit(2)

inspector = inspect(engine)

def main():
    for tablename, table in Base.metadata.tables.items():
        if not inspector.has_table(tablename):
            print(f"Skipping {tablename}: table not present in DB")
            continue
        existing_cols = {c['name'] for c in inspector.get_columns(tablename)}
        for col in table.columns:
            if col.name in existing_cols:
                continue
            try:
                print(f"Adding column {col.name} to {tablename}...")
                col.create(bind=engine, checkfirst=True)
                print(f"Added {col.name}")
            except Exception:
                print(f"Failed to add column {col.name} to {tablename}:")
                traceback.print_exc()

if __name__ == '__main__':
    main()
