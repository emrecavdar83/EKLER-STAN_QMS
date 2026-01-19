import pandas as pd
from sqlalchemy import create_engine, text
import os

def get_db_url():
    possible_paths = [
        "C:\\Users\\GIDA MÜHENDİSİ\\.streamlit\\secrets.toml",
        ".streamlit/secrets.toml"
    ]
    for p in possible_paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    if "DB_URL" in line:
                        return line.split("=", 1)[1].strip().replace('"', '').replace("'", "")
    return 'sqlite:///ekleristan_local.db'

db_url = get_db_url()
print(f"Bağlantı: {'Supabase (Cloud)' if 'supabase' in db_url else 'Local SQLite'}")

engine = create_engine(db_url)

with engine.connect() as conn:
    print("\n--- ÜRÜN TABLOSU SÜTUNLARI ---")
    try:
        # Tablo yapısını kontrol et
        df_cols = pd.read_sql("SELECT column_name FROM information_schema.columns WHERE table_name = 'ayarlar_urunler'", conn)
        print(df_cols['column_name'].tolist())
    except Exception as e:
        print(f"Hata (belki SQLite): {e}")
        # SQLite için fallback
        df_test = pd.read_sql("SELECT * FROM ayarlar_urunler LIMIT 1", conn)
        print(df_test.columns.tolist())
    
    print("\n--- SORUMLU_DEPARTMAN DURUMU ---")
    try:
        df = pd.read_sql("SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler", conn)
        bos_sayisi = df['sorumlu_departman'].isna().sum() + (df['sorumlu_departman'] == '').sum()
        dolu_sayisi = len(df) - bos_sayisi
        print(f"Toplam Ürün: {len(df)}")
        print(f"Departmanı BOŞ Olan: {bos_sayisi}")
        print(f"Departmanı DOLU Olan: {dolu_sayisi}")
        
        if dolu_sayisi > 0:
            print("\n--- ATANMIŞ ÜRÜNLER (Örnek) ---")
            print(df[df['sorumlu_departman'].notna() & (df['sorumlu_departman'] != '')].head(5).to_string())
    except Exception as e:
        print(f"sorumlu_departman sütunu bulunamadı veya hata: {e}")
