import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

# --- YAPILANDIRMA ---
LOCAL_DB = "sqlite:///ekleristan_local.db"
SECRETS_PATH = ".streamlit/secrets.toml"

# Eşleştirme Sözlüğü
SHIFT_MAPPING = {
    '07:00 / 15:00': 'GÜNDÜZ VARDİYASI',
    '08:00 / 18:00': 'GÜNDÜZ VARDİYASI',
    '15:00 / 23:00': 'ARA VARDİYA',
    'Gündüz Vardiyası': 'GÜNDÜZ VARDİYASI',
    'Ara Vardiya': 'ARA VARDİYA',
    'GECE VARDİYASI': 'GECE VARDİYASI',
    'GÜNDÜZ VARDİYASI': 'GÜNDÜZ VARDİYASI',
    'ARA VARDİYA': 'ARA VARDİYA',
    'GECE VARDİYASI': 'GECE VARDİYASI',
    'GNDZ VARDYASI': 'GÜNDÜZ VARDİYASI',
    'ARA VARDYA': 'ARA VARDİYA',
    'GECE VARDYASI': 'GECE VARDİYASI'
}

TABLES_WITH_SHIFT = [
    'personel', 
    'personnel', 
    'hijyen_kontrol_kayitlari', 
    'depo_giris_kayitlari', 
    'urun_kpi_kontrol', 
    'personel_vardiya_programi'
]

def get_live_engine():
    try:
        with open(SECRETS_PATH, "r", encoding="utf-8") as f:
            secrets = toml.load(f)
            url = None
            if "streamlit" in secrets and "DB_URL" in secrets["streamlit"]:
                url = secrets["streamlit"]["DB_URL"]
            elif "DB_URL" in secrets:
                url = secrets["DB_URL"]
                
            if url:
                if url.startswith('"') and url.endswith('"'):
                    url = url[1:-1]
                return create_engine(url)
            raise ValueError("DB_URL bulunamadı.")
    except Exception as e:
        print(f"Canlı veritabanı bağlantı hatası: {e}")
        return None

def standardize_db(engine, db_type="Lokal"):
    print(f"\n--- {db_type} Veritabanı Güncelleniyor ---")
    with engine.begin() as conn:
        for table in TABLES_WITH_SHIFT:
            try:
                # Önce mevcut değerleri al
                df = pd.read_sql(f"SELECT distinct vardiya FROM {table}", conn)
                for _, row in df.iterrows():
                    val = row['vardiya']
                    if not val: continue
                    
                    # Eşleşme var mı?
                    new_val = None
                    for old_pattern, target in SHIFT_MAPPING.items():
                        if old_pattern.upper() in str(val).upper():
                            new_val = target
                            break
                    
                    if new_val:
                        sql = text(f"UPDATE {table} SET vardiya = :nv WHERE vardiya = :ov")
                        conn.execute(sql, {"nv": new_val, "ov": val})
                        print(f"[{table}] {val} -> {new_val} güncellendi.")
            except Exception as e:
                print(f"[{table}] Hatası: {e}")

if __name__ == "__main__":
    from sync_manager import SyncManager
    
    # 1. Lokal Güncelleme
    local_engine = create_engine(LOCAL_DB)
    standardize_db(local_engine, "Lokal")
    
    # 2. Canlı Güncelleme
    print("\n--- Canlı Veritabanı Hazırlanıyor ---")
    try:
        sm = SyncManager()
        if sm.live_engine:
            standardize_db(sm.live_engine, "Canlı")
        sm.dispose()
    except Exception as e:
        print(f"Canlı veritabanı senkronizasyon hatası: {e}")
    
    print("\nİşlem tamamlandı.")
