"""Auto-apply Alembic migrations by creating any missing core tables from models.

This script runs `alembic upgrade heads` repeatedly. If a migration fails due to
a missing relation (UndefinedTable), it will create the specific table from the
SQLAlchemy model metadata and retry. If a migration fails because a table
already exists (DuplicateTable), it will `alembic stamp <revision>` to mark the
revision as applied and continue.

Usage (from repo root):
  $env:DATABASE_URL = '<postgres://...>'
  python backend/scripts/auto_apply_migrations.py
"""
import os
import sys
import re
import subprocess
import time
import traceback

# Ensure backend dir on sys.path so we can import app
HERE = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
BACKEND_DIR = os.path.join(REPO_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

try:
    from app.db.base import Base
    import app.db.models  # register models
    from app.db.session import engine
except Exception:
    print("Failed to import app models; ensure DATABASE_URL is set and backend package is importable.")
    traceback.print_exc()
    sys.exit(2)


ALEMBIC_CMD = ["alembic", "-c", "alembic.ini", "upgrade", "heads"]
ALEMBIC_STAMP = ["alembic", "-c", "alembic.ini", "stamp"]

def run_alembic():
    proc = subprocess.run(ALEMBIC_CMD, cwd=BACKEND_DIR, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr

def stamp_revision(rev: str):
    proc = subprocess.run(ALEMBIC_STAMP + [rev], cwd=BACKEND_DIR, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr

def create_table_by_name(tablename: str) -> bool:
    tbl = Base.metadata.tables.get(tablename)
    if tbl is None:
        print(f"Model metadata for table '{tablename}' not found.")
        return False
    print(f"Creating table '{tablename}' from model metadata...")
    try:
        tbl.create(bind=engine)
        print(f"Created table '{tablename}'.")
        return True
    except Exception:
        print(f"Failed to create table '{tablename}':")
        traceback.print_exc()
        return False


def main():
    max_iters = 30
    for attempt in range(max_iters):
        print(f"Alembic attempt {attempt+1}/{max_iters}...")
        code, out, err = run_alembic()
        combined = out + "\n" + err
        if code == 0:
            print("Alembic migrations applied successfully.")
            return 0

        # Look for UndefinedTable: relation "<table>" does not exist
        m = re.search(r"relation \"(?P<table>[\w_]+)\" does not exist", combined)
        if m:
            table = m.group("table")
            print(f"Migration failed due to missing table: {table}")
            ok = create_table_by_name(table)
            if not ok:
                print("Cannot auto-create missing table; aborting.")
                return 3
            # small pause before retry
            time.sleep(0.5)
            continue

        # Look for DuplicateTable errors -> mark the migration revision as applied
        if "DuplicateTable" in combined or "already exists" in combined:
            # Attempt to extract target revision from Alembic output line like:
            # Running upgrade a1b2 -> a1b3, Description
            # Try to extract the target revision token from the Alembic output.
            rm = re.search(r"Running upgrade .* -> (?P<rev>[^,\s]+)", combined)
            rev = None
            if rm:
                candidate = rm.group("rev")
                # If candidate contains a hex revision id, extract it.
                hexm = re.search(r"([0-9a-fA-F]{6,40})", candidate)
                if hexm:
                    rev = hexm.group(1)
                else:
                    # Fallback: search entire output for a hex-like revision id.
                    hexm2 = re.search(r"([0-9a-fA-F]{6,40})", combined)
                    if hexm2:
                        rev = hexm2.group(1)

            if rev:
                print(f"Detected DuplicateTable; stamping revision {rev} as applied.")
                scode, sout, serr = stamp_revision(rev)
                if scode == 0:
                    print(f"Stamped {rev} successfully.")
                    time.sleep(0.2)
                    continue
                else:
                    print(f"Failed to stamp revision {rev}:", sout, serr)
                    return 4
            else:
                print("DuplicateTable encountered but could not determine revision to stamp.")
                print(combined)
                return 5

        # Unhandled error
        print("Unhandled Alembic error:\n", combined)
        return 6

    print("Exceeded maximum attempts to auto-apply migrations.")
    return 7


if __name__ == "__main__":
    sys.exit(main())
