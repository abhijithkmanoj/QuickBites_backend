from pathlib import Path
import re
import sys
from sqlalchemy import create_engine

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / '.env'
if not ENV_PATH.exists():
    print('backend/.env not found')
    sys.exit(1)

text = ENV_PATH.read_text(encoding='utf-8')
match = re.search(r'^DATABASE_URL=(.+)$', text, flags=re.MULTILINE)
if not match:
    print('DATABASE_URL not found in backend/.env')
    sys.exit(1)
url = match.group(1).strip()
print('Using DATABASE_URL:', url)

# Import application metadata after adding backend root to sys.path
sys.path.append(str(BASE_DIR))
from app.db.base import Base
from app.db import models  # noqa: F401

engine = create_engine(url, future=True)
print('Creating all tables from model metadata...')
Base.metadata.create_all(engine)
print('Schema created successfully.')
