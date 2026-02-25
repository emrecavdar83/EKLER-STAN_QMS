import sqlite3
import os

DB_PATH = 'ekleristan_local.db'

def fix_db():
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Define the core SOSTS tables with correct SQLite schemas
    tables_sql = {
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
        """
    }

    print("Fixing soguk_odalar with NULL handling...")
    try:
        cursor.execute("DROP TABLE IF EXISTS soguk_odalar_new")
        cursor.execute(tables_sql["soguk_odalar"])
        
        # Manually select columns and provide defaults for potential NULLs in the broken table
        cursor.execute("""
            INSERT INTO soguk_odalar_new (
                oda_kodu, oda_adi, departman, min_sicaklik, max_sicaklik, 
                sapma_takip_dakika, olcum_sikligi, qr_token, qr_uretim_tarihi, 
                aktif, olusturulma_tarihi
            ) 
            SELECT 
                COALESCE(oda_kodu, 'UNKNOWN_' || ROW_NUMBER() OVER(ORDER BY oda_adi)), 
                COALESCE(oda_adi, 'Tanımsız Oda'), 
                departman, 
                COALESCE(min_sicaklik, 0.0), 
                COALESCE(max_sicaklik, 4.0), 
                COALESCE(sapma_takip_dakika, 30), 
                COALESCE(olcum_sikligi, 2), 
                qr_token, 
                qr_uretim_tarihi, 
                COALESCE(aktif, 1), 
                COALESCE(olusturulma_tarihi, CURRENT_TIMESTAMP)
            FROM soguk_odalar
        """)
        
        cursor.execute("DROP TABLE soguk_odalar")
        cursor.execute("ALTER TABLE soguk_odalar_new RENAME TO soguk_odalar")
        print("Successfully fixed soguk_odalar")
    except Exception as e:
        print(f"Failed to fix soguk_odalar: {e}")

    conn.commit()
    conn.close()
    print("Repair finished.")

if __name__ == "__main__":
    fix_db()
