import sqlite3
import os

DB_PATH = 'ekleristan_local.db'

def fix_constraints():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("Fixing olcum_plani constraints...")
    try:
        # 1. Create temporary table with unique constraint
        cursor.execute("""
            CREATE TABLE olcum_plani_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oda_id INTEGER NOT NULL,
                beklenen_zaman DATETIME NOT NULL,
                gerceklesen_olcum_id INTEGER,
                durum TEXT DEFAULT 'BEKLIYOR',
                guncelleme_zamani DATETIME,
                UNIQUE(oda_id, beklenen_zaman)
            )
        """)

        # 2. Copy data (skip duplicates if any, though likely none yet)
        cursor.execute("""
            INSERT OR IGNORE INTO olcum_plani_new (
                oda_id, beklenen_zaman, gerceklesen_olcum_id, durum, guncelleme_zamani
            )
            SELECT oda_id, beklenen_zaman, gerceklesen_olcum_id, durum, guncelleme_zamani
            FROM olcum_plani
        """)

        # 3. Swap tables
        cursor.execute("DROP TABLE olcum_plani")
        cursor.execute("ALTER TABLE olcum_plani_new RENAME TO olcum_plani")
        
        print("Successfully added UNIQUE constraint to olcum_plani")
    except Exception as e:
        print(f"Failed to fix constraints: {e}")

    conn.commit()
    conn.close()
    print("Constraint fix complete.")

if __name__ == "__main__":
    fix_constraints()
