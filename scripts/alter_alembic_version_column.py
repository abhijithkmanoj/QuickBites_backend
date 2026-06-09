"""Ensure alembic_version.version_num column can hold long revision identifiers.

This script alters the column type to VARCHAR(255) if it's smaller.
"""
import os
import psycopg2

url = os.environ.get("DATABASE_URL")
if not url:
    raise SystemExit("DATABASE_URL not set")

sql = """
DO $$
BEGIN
    IF (SELECT character_maximum_length FROM information_schema.columns
        WHERE table_name = 'alembic_version' AND column_name = 'version_num') < 255 THEN
        ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255);
    END IF;
EXCEPTION WHEN undefined_table THEN
    -- If alembic_version doesn't exist yet, create it with adequate size
    CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(255) NOT NULL);
END$$;
"""

conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute(sql)
conn.commit()
cur.close()
conn.close()
print("alembic_version column ensured to accept long revision ids")
