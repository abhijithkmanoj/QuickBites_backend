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
            to_drop = ['order_items', 'payments', 'orders', 'addresses']
            for t in to_drop:
                cur.execute(f"DROP TABLE IF EXISTS {t} CASCADE;")
                print(f'Dropped table {t} (if existed)')
except Exception as e:
    print('Error dropping table:', e)
    raise
