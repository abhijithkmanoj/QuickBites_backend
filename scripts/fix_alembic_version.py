from dotenv import load_dotenv
import os
load_dotenv('../backend/.env' if os.path.exists('../backend/.env') else 'backend/.env')
url=os.environ.get('DATABASE_URL') or os.environ.get('POSTGRES_URL')
if not url:
    print('NO_DB')
    raise SystemExit(1)
url=url.replace('+psycopg','')
import psycopg
print('connecting to', url)
conn=psycopg.connect(url)
cur=conn.cursor()
try:
    cur.execute("ALTER TABLE alembic_version ALTER COLUMN version_num TYPE varchar(255);")
    conn.commit()
    print('ALTER_OK')
except Exception as e:
    print('ERR', type(e).__name__, e)
    raise
finally:
    cur.close(); conn.close()
