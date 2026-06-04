import os
import sqlite3

root = os.path.abspath('.')
for dirpath, dirnames, filenames in os.walk(root):
    for fn in filenames:
        if fn.endswith('.db'):
            path = os.path.join(dirpath, fn)
            try:
                conn = sqlite3.connect(path)
                cur = conn.cursor()
                try:
                    cur.execute("SELECT id, email FROM users WHERE email = ?", ('fivestar@gmail.com',))
                    u = cur.fetchone()
                except Exception:
                    u = None
                try:
                    cur.execute("SELECT id, name FROM restaurants WHERE name = ?", ('Five Star',))
                    r = cur.fetchone()
                except Exception:
                    r = None
                conn.close()
                if u or r:
                    print(path, 'user=', u, 'restaurant=', r)
            except Exception:
                pass
