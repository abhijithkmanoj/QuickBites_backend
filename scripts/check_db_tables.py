from pathlib import Path
import re
from sqlalchemy import create_engine, inspect

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / '.env'
text = ENV_PATH.read_text(encoding='utf-8')
match = re.search(r'^DATABASE_URL=(.+)$', text, flags=re.MULTILINE)
if not match:
    raise SystemExit('DATABASE_URL not found in backend/.env')
url = match.group(1).strip()
print('Using DATABASE_URL:', url)
# Ensure Psycopg v3 driver (not psycopg2)
if url.startswith('postgresql://'):
    url = url.replace('postgresql://', 'postgresql+psycopg://', 1)
engine = create_engine(url, future=True)
inspector = inspect(engine)
print('tables:', inspector.get_table_names())
