# -*- coding: utf-8 -*-
import pandas as pd
from sqlalchemy import create_engine, text
import toml

# Bağlantı
try:
    secrets = toml.load('.streamlit/secrets.toml')
    url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
    url = url.strip('"')
    print(f"Connecting to DB...")
    engine = create_engine(url)
except:
    engine = create_engine('sqlite:///ekleristan_local.db')

def check_data():
    print("--- BOMBA Ürünleri Veri Kontrolü ---")
    
    sql = text("SELECT * FROM ayarlar_urunler WHERE sorumlu_departman ILIKE :p")
    try:
        df = pd.read_sql(sql, engine, params={"p": "%BOMBA%"})
        if not df.empty:
            print(f"Toplam {len(df)} BOMBA ürünü bulundu.")
            # Kritik kolonları kontrol et
            cols = ['urun_adi', 'numune_sayisi', 'raf_omru_gun', 'sorumlu_departman']
            existing_cols = [c for c in cols if c in df.columns]
            
            print("\nÖrnek Veriler:")
            print(df[existing_cols].head().to_string())
            
            print("\nVeri Tipi Analizi:")
            for c in existing_cols:
                print(f"- {c}: {df[c].dtype}")
                # None/Null kontrolü
                null_count = df[c].isnull().sum()
                if null_count > 0:
                    print(f"  ⚠️ {null_count} adet NULL değer var!")
                    
        else:
            print("❌ BOMBA departmanına ait ürün bulunamadı!")
            
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    check_data()
