"""Add missing user profile columns using plain SQL (safe, idempotent).
"""
import os
import psycopg2

url = os.environ.get('DATABASE_URL')
if not url:
    raise SystemExit('DATABASE_URL not set')

sql = '''
ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS date_of_birth TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS gender VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS language_preference VARCHAR(10) DEFAULT 'en';
ALTER TABLE users ADD COLUMN IF NOT EXISTS notification_preference JSON;
ALTER TABLE users ADD COLUMN IF NOT EXISTS privacy_settings JSON;
ALTER TABLE users ADD COLUMN IF NOT EXISTS theme_preference VARCHAR(20) DEFAULT 'system';
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_active_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image VARCHAR(255);
'''

conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute(sql)
conn.commit()
cur.close()
conn.close()
print('User profile columns ensured')
