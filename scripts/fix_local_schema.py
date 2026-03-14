import sqlite3

DB_PATH = "ekleristan_local.db"

def fix_schema():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. PERSONEL Table
    print("Inspecting 'personel' table...")
    cursor.execute("PRAGMA table_info(personel)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "vardiya" not in columns:
        print("Adding 'vardiya' column to 'personel'...")
        cursor.execute("ALTER TABLE personel ADD COLUMN vardiya TEXT")
        
    # 2. AYARLAR_YETKILER Table
    print("Inspecting 'ayarlar_yetkiler' table...")
    cursor.execute("PRAGMA table_info(ayarlar_yetkiler)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "sadece_kendi_bolumu" not in columns:
        print("Adding 'sadece_kendi_bolumu' column to 'ayarlar_yetkiler'...")
        # SQLite doesn't support BOOLEAN natively, uses INTEGER (0/1)
        cursor.execute("ALTER TABLE ayarlar_yetkiler ADD COLUMN sadece_kendi_bolumu INTEGER DEFAULT 0")
        
    conn.commit()
    conn.close()
    print("Schema fix complete.")

if __name__ == "__main__":
    fix_schema()
