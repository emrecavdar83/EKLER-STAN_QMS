import sqlite3
import os

def bootstrap_local():
    db_path = 'ekleristan_local.db'
    if not os.path.exists(db_path):
        print("Local DB not found.")
        return
        
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Run the same migration (simplified for SQLite if needed, but the SQL is compatible enough)
    sql_file = "migrations/20260318_qdms_schema.sql"
    with open(sql_file, "r", encoding="utf-8") as f:
        script = f.read()
    
    # Remove SERIAL (replace with INTEGER PRIMARY KEY AUTOINCREMENT if needed, 
    # but the SQL script already has basic table creations)
    # The script uses SERIAL, which SQLite doesn't support by default, 
    # but I'll only run the INSERTs if the tables already exist or fix them.
    
    try:
        # 1. Ensure Infrastructure Tables (Mirroring Supabase)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ayarlar_moduller (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modul_anahtari TEXT NOT NULL UNIQUE,
            modul_etiketi TEXT NOT NULL,
            aktif INTEGER DEFAULT 1,
            sira_no INTEGER
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ayarlar_yetkiler (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rol_adi TEXT,
            modul_adi TEXT,
            erisim_turu TEXT,
            sadece_kendi_bolumu INTEGER DEFAULT 0
        )""")
        
        # 2. Run the main migration script
        cur.executescript(script.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT").replace("ON CONFLICT DO NOTHING", "").replace("ON CONFLICT (modul_anahtari) DO UPDATE SET aktif = 1", ""))
        
        # SQLite doesn't handle ON CONFLICT the same way, so let's just do a simple insertion
        # and ignore errors if they exist for the bootstrap.
        # Actually, executescript is enough for basic INSERTs.
        
        conn.commit()
        print("Local bootstrap completed.")
    except Exception as e:
        print(f"Local bootstrap error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    bootstrap_local()
