from pathlib import Path
import re
from sqlalchemy import create_engine, inspect

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / '.env'
text = ENV_PATH.read_text(encoding='utf-8')
source_match = re.search(r'^DATABASE_SOURCE_URL=(.+)$', text, flags=re.MULTILINE)
if not source_match:
    raise SystemExit('DATABASE_SOURCE_URL not found in backend/.env')
source_url = source_match.group(1).strip()
print('Source DB:', source_url)
engine = create_engine(source_url, future=True)
inspector = inspect(engine)
print('source tables:', inspector.get_table_names())
