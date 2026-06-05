from pathlib import Path
import re
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / '.env'
text_content = ENV_PATH.read_text(encoding='utf-8')
source_match = re.search(r'^DATABASE_SOURCE_URL=(.+)$', text_content, flags=re.MULTILINE)
if not source_match:
    raise SystemExit('DATABASE_SOURCE_URL not found in backend/.env')
source_url = source_match.group(1).strip()
engine = create_engine(source_url, future=True)
with engine.connect() as conn:
    result = conn.execute(text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_type='BASE TABLE' ORDER BY table_schema, table_name"))
    rows = result.fetchall()
    if not rows:
        print('No tables found in source database')
    else:
        for schema, table in rows:
            print(schema, table)
