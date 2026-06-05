from pathlib import Path
import re
import sys

env_path = Path(__file__).resolve().parents[1] / '.env'
if not env_path.exists():
    print('backend/.env not found')
    sys.exit(1)
text = env_path.read_text(encoding='utf-8')
match = re.search(r'^DATABASE_URL=(.+)$', text, flags=re.MULTILINE)
if not match:
    print('DATABASE_URL not found in backend/.env')
    sys.exit(1)
url = match.group(1).strip()
print('Using DATABASE_URL:', url)

import psycopg
try:
    with psycopg.connect(url, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public';")
            tables = [row[0] for row in cur.fetchall()]
            if not tables:
                print('No tables found in public schema')
            else:
                print('Tables to drop:', tables)
                for t in tables:
                    cur.execute(f'DROP TABLE IF EXISTS "{t}" CASCADE;')
                    print('Dropped', t)
except Exception as e:
    print('Error wiping schema:', e)
    raise
