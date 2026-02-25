import sqlite3
import os

DB_PATH = 'ekleristan_local.db'

def fix_db():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    tables = {
        "soguk_odalar": """
            CREATE TABLE soguk_odalar_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oda_kodu TEXT UNIQUE NOT NULL,
                oda_adi TEXT NOT NULL,
                departman TEXT,
                min_sicaklik REAL NOT NULL DEFAULT 0.0,
                max_sicaklik REAL NOT NULL DEFAULT 4.0,
                sapma_takip_dakika INTEGER NOT NULL DEFAULT 30,
                olcum_sikligi INTEGER NOT NULL DEFAULT 2,
                qr_token TEXT UNIQUE,
                qr_uretim_tarihi DATETIME,
                aktif INTEGER DEFAULT 1,
                olusturulma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "sicaklik_olcumleri": """
            CREATE TABLE sicaklik_olcumleri_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oda_id INTEGER NOT NULL,
                sicaklik_degeri REAL NOT NULL,
                olcum_zamani DATETIME DEFAULT CURRENT_TIMESTAMP,
                planlanan_zaman DATETIME,
                qr_ile_girildi INTEGER DEFAULT 1,
                kaydeden_kullanici TEXT,
                sapma_var_mi INTEGER DEFAULT 0,
                sapma_aciklamasi TEXT,
                olusturulma_tarihi DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        "olcum_plani": """
            CREATE TABLE olcum_plani_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                oda_id INTEGER NOT NULL,
                beklenen_zaman DATETIME NOT NULL,
                gerceklesen_olcum_id INTEGER,
                durum TEXT DEFAULT 'BEKLIYOR',
                guncelleme_zamani DATETIME
            )
        """
    }

    for table, create_sql in tables.items():
        print(f"Fixing {table}...")
        try:
            # Get existing columns
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [row[1] for row in cursor.fetchall()]
            if not cols:
                print(f"Table {table} does not exist. Skipping.")
                continue

            # Create new table
            cursor.execute(create_sql)

            # Copy data, omitting id if it might be null or duplicating it if it's fine
            col_list = ", ".join([c for c in cols if c != 'id'])
            cursor.execute(f"INSERT INTO {table}_new ({col_list}) SELECT {col_list} FROM {table}")

            # Swap tables
            cursor.execute(f"DROP TABLE {table}")
            cursor.execute(f"ALTER TABLE {table}_new RENAME TO {table}")
            print(f"Successfully fixed {table}")
        except Exception as e:
            print(f"Error fixing {table}: {e}")

    conn.commit()
    conn.close()
    print("Database fix complete.")

if __name__ == "__main__":
    fix_db()
