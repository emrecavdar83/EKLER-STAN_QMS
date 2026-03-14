import sqlite3
import os

DB_PATH = "ekleristan_local.db"

def inspect():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found!")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- TABLES ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print(tables)
    
    if "map_vardiya" in tables:
        print("\n--- SHIFTS IN MAP_VARDIYA ---")
        cursor.execute("SELECT * FROM map_vardiya ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        cols = [description[0] for description in cursor.description]
        for r in rows:
            print(dict(zip(cols, r)))
    else:
        print("\nWARNING: map_vardiya table NOT found!")

    conn.close()

if __name__ == "__main__":
    inspect()
