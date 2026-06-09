import os
import psycopg2

url = os.environ.get('DATABASE_URL')
if not url:
    raise SystemExit('DATABASE_URL not set')

sql = '''
CREATE TABLE IF NOT EXISTS users (
    id uuid PRIMARY KEY,
    name varchar(120) NOT NULL,
    email varchar(255) NOT NULL UNIQUE,
    phone varchar(20),
    password_hash varchar(255) NOT NULL,
    role varchar(50) NOT NULL DEFAULT 'customer',
    is_active boolean DEFAULT true,
    created_at timestamp DEFAULT now(),
    updated_at timestamp DEFAULT now()
);
'''

conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute(sql)
conn.commit()
cur.close()
conn.close()
print('users table ensured')
