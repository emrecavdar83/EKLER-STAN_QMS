import sqlite3
import sqlalchemy
from sqlalchemy import create_engine, text
import toml
import os
from datetime import datetime

LOCAL_DB = "sqlite:///ekleristan_local.db"
SECRETS_FILE = ".streamlit/secrets.toml"

def audit_timestamps():
    print("Personel zaman damgası denetimi başlatılıyor...")
    
    # 1. Local DB Audit
    print("\n--- Yerel Veritabanı (SQLite) ---")
    local_engine = create_engine(LOCAL_DB)
    with local_engine.connect() as conn:
        try:
            # Check for NULL update dates
            res = conn.execute(text("SELECT COUNT(*) FROM personel WHERE guncelleme_tarihi IS NULL OR guncelleme_tarihi = ''")).scalar()
            print(f"Eksik zaman damgalı personel sayısı: {res}")
            
            if res > 0:
                baseline = "2026-01-01 00:00:00"
                conn.execute(text(f"UPDATE personel SET guncelleme_tarihi = :ts WHERE guncelleme_tarihi IS NULL OR guncelleme_tarihi = ''"), {"ts": baseline})
                conn.commit()
                print(f"OK: {res} kayıt '{baseline}' olarak güncellendi.")
        except Exception as e:
            print(f"HATA: Yerel veritabanı hatası: {e}")

    # 2. Live DB Audit
    print("\n--- Bulut Veritabanı (PostgreSQL) ---")
    try:
        secrets = toml.load(SECRETS_FILE)
        url = secrets.get('streamlit', {}).get('DB_URL', secrets.get('DB_URL'))
        if url.startswith('"') and url.endswith('"'):
            url = url[1:-1]
        live_engine = create_engine(url)
        
        with live_engine.connect() as conn:
            # Check for NULL update dates
            res = conn.execute(text("SELECT COUNT(*) FROM personel WHERE guncelleme_tarihi IS NULL")).scalar()
            print(f"Eksik zaman damgalı personel sayısı: {res}")
            
            if res > 0:
                baseline = datetime(2026, 1, 1, 0, 0, 0)
                conn.execute(text("UPDATE personel SET guncelleme_tarihi = :ts WHERE guncelleme_tarihi IS NULL"), {"ts": baseline})
                conn.commit()
                print(f"OK: {res} kayıt '{baseline}' olarak güncellendi.")
            else:
                print("✓ Eksik kayıt bulunmadı.")
    except Exception as e:
        print(f"HATA: Bulut veritabanı hatası: {e}")

if __name__ == "__main__":
    audit_timestamps()
