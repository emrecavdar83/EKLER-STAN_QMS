import toml
import os
from sqlalchemy import create_engine, text, inspect
import sqlite3

def align_live_schema():
    print("--- Bulut Şema Hizalama (Local -> Live) Başlıyor ---")
    try:
        # Load secrets
        secrets_path = os.path.join(os.getcwd(), '.streamlit', 'secrets.toml')
        secrets = toml.load(secrets_path)
        url = secrets.get('streamlit', {}).get('DB_URL', secrets.get('DB_URL'))
        if url.startswith('"') and url.endswith('"'):
            url = url[1:-1]
        
        live_engine = create_engine(url)
        
        # 1. MISSING TABLES (SOSTS)
        # We define the SQL for missing tables based on local schema
        sosts_ddl = [
            """
            CREATE TABLE IF NOT EXISTS soguk_odalar (
                id SERIAL PRIMARY KEY,
                oda_kodu TEXT UNIQUE NOT NULL,
                oda_adi TEXT NOT NULL,
                departman TEXT,
                min_sicaklik REAL NOT NULL DEFAULT 0.0,
                max_sicaklik REAL NOT NULL DEFAULT 4.0,
                sapma_takip_dakika INTEGER NOT NULL DEFAULT 30,
                olcum_sikligi INTEGER NOT NULL DEFAULT 2,
                qr_token TEXT UNIQUE NOT NULL,
                qr_uretim_tarihi TIMESTAMP,
                aktif INTEGER DEFAULT 1,
                olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sicaklik_olcumleri (
                id SERIAL PRIMARY KEY,
                oda_id INTEGER NOT NULL,
                sicaklik_degeri REAL NOT NULL,
                olcum_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                planlanan_zaman TIMESTAMP,
                qr_ile_girildi INTEGER DEFAULT 1,
                kaydeden_kullanici TEXT,
                sapma_var_mi INTEGER DEFAULT 0,
                sapma_aciklamasi TEXT,
                olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS olcum_plani (
                id SERIAL PRIMARY KEY,
                oda_id INTEGER NOT NULL,
                beklenen_zaman TIMESTAMP NOT NULL,
                gerceklesen_olcum_id INTEGER,
                durum TEXT DEFAULT 'BEKLIYOR',
                guncelleme_zamani TIMESTAMP
            )
            """
        ]
        
        with live_engine.begin() as conn:
            print("Tablolar oluşturuluyor/güncelleniyor...")
            for sql in sosts_ddl:
                conn.execute(text(sql))
            
            # 2. MISSING COLUMNS (Common Tables)
            # Based on schema_report.json
            alterations = [
                ("temizlik_kayitlari", "dogrulama_tipi", "TEXT"),
                ("kimyasal_envanter", "olusturma_tarihi", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                ("hijyen_kontrol_kayitlari", "genel_karar", "TEXT"),
                ("hijyen_kontrol_kayitlari", "id", "SERIAL"), # SERIAL adds auto-increment
                ("ayarlar_temizlik_plani", "id", "SERIAL") 
            ]
            
            inspector = inspect(live_engine)
            for table, col, dtype in alterations:
                columns = [c['name'] for c in inspector.get_columns(table)]
                if col not in columns:
                    print(f"Adding {col} to {table}...")
                    try:
                        # For primary keys, try to add without PRIMARY KEY constraint first, 
                        # or just add as a column. In Postgres, serial handles it.
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {dtype}"))
                    except Exception as e:
                        print(f"Error adding {col} on {table}: {e}")
                else:
                    print(f"✅ {table}.{col} already exists.")

        print("✅ Bulut şeması başarıyla hizalandı.")
        
    except Exception as e:
        print(f"KRİTİK HATA: {e}")

if __name__ == "__main__":
    align_live_schema()
