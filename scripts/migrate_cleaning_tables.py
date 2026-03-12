from sqlalchemy import create_engine, text

db_url = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
engine = create_engine(db_url)

def run_migration():
    commands = [
        # --- 1. ayarlar_temizlik_plani tablosu tahkimatı ---
        "ALTER TABLE ayarlar_temizlik_plani ADD COLUMN IF NOT EXISTS kat_id INTEGER;",
        "ALTER TABLE ayarlar_temizlik_plani ADD COLUMN IF NOT EXISTS bolum_id INTEGER;",
        "ALTER TABLE ayarlar_temizlik_plani ADD COLUMN IF NOT EXISTS hat_id INTEGER;",
        "ALTER TABLE ayarlar_temizlik_plani ADD COLUMN IF NOT EXISTS ekipman_id INTEGER;",
        "ALTER TABLE ayarlar_temizlik_plani ADD COLUMN IF NOT EXISTS is_migrated BOOLEAN DEFAULT FALSE;",
        
        # --- 2. tanim_ekipmanlar tablosuna ID ekle ---
        "ALTER TABLE tanim_ekipmanlar ADD COLUMN IF NOT EXISTS id SERIAL;",
        
        # --- 3. temizlik_kayitlari tablosu tahkimatı (Snapshot) ---
        "ALTER TABLE temizlik_kayitlari ADD COLUMN IF NOT EXISTS lokasyon_id INTEGER;",
        "ALTER TABLE temizlik_kayitlari ADD COLUMN IF NOT EXISTS ekipman_id INTEGER;",
        "ALTER TABLE temizlik_kayitlari ADD COLUMN IF NOT EXISTS lokasyon_snapshot TEXT;",
        "ALTER TABLE temizlik_kayitlari ADD COLUMN IF NOT EXISTS ekipman_snapshot TEXT;",
        
        # --- 3. Yedekleme (Anayasa m.10 Önlemi) ---
        "CREATE TABLE IF NOT EXISTS ayarlar_temizlik_plani_backup_v4 AS SELECT * FROM ayarlar_temizlik_plani;"
    ]
    
    with engine.begin() as conn:
        for cmd in commands:
            print(f"Executing: {cmd}")
            conn.execute(text(cmd))
    print("Migration completed successfully.")

if __name__ == "__main__":
    run_migration()
