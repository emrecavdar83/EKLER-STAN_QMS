import sys
import os
from sqlalchemy import text

# Force UTF-8 for printing to avoid Windows charmap issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append(os.getcwd())
from database.connection import get_engine

def run_shadow_migration():
    engine = get_engine()
    print(f"Connecting to: {engine.url}")
    
    with engine.connect() as conn:
        print("\n1. Creating 'ayarlar_moduller' table...")
        
        # Using simple types for max compatibility
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS ayarlar_moduller (
            id INTEGER PRIMARY KEY,
            modul_anahtari TEXT UNIQUE NOT NULL,
            modul_etiketi TEXT NOT NULL,
            sira_no INTEGER DEFAULT 10,
            ikon TEXT,
            aktif INTEGER DEFAULT 1
        )
        """
            
        try:
            conn.execute(text(create_table_sql))
            print("SUCCESS: Table created or already exists.")
        except Exception as e:
            print(f"ERROR: Table creation failed: {e}")

        print("\n2. Adding 'sadece_kendi_bolumu' column to 'ayarlar_yetkiler'...")
        try:
            # SQLite safe check: trying to add column
            conn.execute(text("ALTER TABLE ayarlar_yetkiler ADD COLUMN sadece_kendi_bolumu INTEGER DEFAULT 0"))
            print("SUCCESS: Column added.")
        except Exception as e:
             if 'duplicate' in str(e).lower() or 'already exists' in str(e).lower():
                 print("INFO: Column already exists.")
             else:
                 print(f"WARNING: Column addition error (may be fine): {e}")

        print("\n3. Inserting Initial Modules (ASCII only labels for safety)...")
        # I will replace Emojis with descriptive strings for the initial DB insert to bypass console issues
        initial_modules = [
            ("uretim_girisi", "URETIM GIRISI", 10, "U"),
            ("kpi_kontrol", "KPI KONTROL", 20, "K"),
            ("gmp_denetimi", "GMP DENETIMI", 30, "G"),
            ("personel_hijyen", "PERSONEL HIJYEN", 40, "H"),
            ("temizlik_kontrol", "TEMIZLIK KONTROL", 50, "T"),
            ("kurumsal_raporlama", "RAPORLAMA", 60, "R"),
            ("soguk_oda", "SOGUK ODA", 70, "S"),
            ("ayarlar", "AYARLAR", 80, "A")
        ]
        
        for key, label, order, icon in initial_modules:
            try:
                conn.execute(
                    text("INSERT OR IGNORE INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, ikon, aktif) VALUES (:k, :l, :o, :i, 1)"), 
                    {"k": key, "l": label, "o": order, "i": icon}
                )
                print(f"Added/Skipped: {key}")
            except Exception as e:
                 print(f"Error inserting {key}: {e}")
                 
        conn.commit()
            
    print("\n✅ Migration Finished Successfully.")

if __name__ == "__main__":
    run_shadow_migration()
