import glob
import sqlite3

for path in glob.glob('*.db'):
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM restaurants WHERE name = ?", ('Five Star',))
        row = cur.fetchone()
        conn.close()
        if row:
            print(f"FOUND in {path}: {row}")
    except Exception as e:
        # ignore files that aren't sqlite or don't have the table
        pass
