import sqlite3
import os

db_path = 'ekleristan_local.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cur.fetchall()]
    with open('full_db_dump_utf8.txt', 'w', encoding='utf-8') as f:
        for t in tables:
            f.write(f"TABLE: {t}\n")
            cur.execute(f"PRAGMA table_info({t})")
            for col in cur.fetchall():
                f.write(f"  {col[1]} ({col[2]})\n")
    conn.close()
else:
    print("Database not found.")
