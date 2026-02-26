import sqlite3

def run():
    db_path = 'ekleristan_local.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. tanim_metotlar → metot_adi UNIQUE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tanim_metotlar_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metot_adi TEXT NOT NULL UNIQUE,
                aciklama TEXT
            )
        """)
        
        cursor.execute("""
            INSERT OR IGNORE INTO tanim_metotlar_new (metot_adi, aciklama)
            SELECT metot_adi, aciklama FROM tanim_metotlar
        """)
        
        cursor.execute("DROP TABLE tanim_metotlar")
        cursor.execute("ALTER TABLE tanim_metotlar_new RENAME TO tanim_metotlar")

        # 2. kimyasal_envanter → kimyasal_adi UNIQUE
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kimyasal_envanter_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kimyasal_adi TEXT NOT NULL UNIQUE,
                tedarikci TEXT,
                msds_yolu TEXT,
                tds_yolu TEXT,
                olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            INSERT OR IGNORE INTO kimyasal_envanter_new (kimyasal_adi, tedarikci, msds_yolu, tds_yolu, olusturma_tarihi)
            SELECT kimyasal_adi, tedarikci, msds_yolu, tds_yolu, olusturma_tarihi FROM kimyasal_envanter
        """)
        
        cursor.execute("DROP TABLE kimyasal_envanter")
        cursor.execute("ALTER TABLE kimyasal_envanter_new RENAME TO kimyasal_envanter")
        
        conn.commit()
        print("Success: Migration 002 completed.")
    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    run()
