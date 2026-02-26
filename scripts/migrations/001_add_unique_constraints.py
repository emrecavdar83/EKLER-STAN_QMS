import sqlite3

def run():
    db_path = 'ekleristan_local.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. ayarlar_urunler → urun_adi UNIQUE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ayarlar_urunler_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                urun_adi TEXT NOT NULL UNIQUE,
                raf_omru_gun REAL,
                olcum1_ad TEXT,
                olcum1_min REAL,
                olcum1_max REAL,
                olcum2_ad TEXT,
                olcum2_min REAL,
                olcum2_max REAL,
                olcum3_ad TEXT,
                olcum3_min REAL,
                olcum3_max REAL,
                olcum_sikligi_dk REAL,
                uretim_bolumu TEXT,
                numune_sayisi REAL,
                sorumlu_departman TEXT,
                aktif INTEGER DEFAULT 1
            )
        """)
        
        cursor.execute("""
            INSERT OR IGNORE INTO ayarlar_urunler_new (
                urun_adi, raf_omru_gun, olcum1_ad, olcum1_min, olcum1_max,
                olcum2_ad, olcum2_min, olcum2_max, olcum3_ad, olcum3_min,
                olcum3_max, olcum_sikligi_dk, uretim_bolumu, numune_sayisi,
                sorumlu_departman
            )
            SELECT 
                urun_adi, raf_omru_gun, olcum1_ad, olcum1_min, olcum1_max,
                olcum2_ad, olcum2_min, olcum2_max, olcum3_ad, olcum3_min,
                olcum3_max, olcum_sikligi_dk, uretim_bolumu, numune_sayisi,
                sorumlu_departman
            FROM ayarlar_urunler
        """)

        cursor.execute("DROP TABLE ayarlar_urunler")
        cursor.execute("ALTER TABLE ayarlar_urunler_new RENAME TO ayarlar_urunler")

        # 2. urun_parametreleri → (urun_adi, parametre_adi) UNIQUE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS urun_parametreleri_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                urun_adi TEXT,
                parametre_adi TEXT,
                min_deger REAL,
                max_deger REAL,
                UNIQUE(urun_adi, parametre_adi)
            )
        """)
        
        cursor.execute("""
            INSERT OR IGNORE INTO urun_parametreleri_new (id, urun_adi, parametre_adi, min_deger, max_deger)
            SELECT id, urun_adi, parametre_adi, min_deger, max_deger
            FROM urun_parametreleri
        """)
        
        cursor.execute("DROP TABLE urun_parametreleri")
        cursor.execute("ALTER TABLE urun_parametreleri_new RENAME TO urun_parametreleri")
        
        conn.commit()
        print("Success: Migration 001 completed.")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run()
