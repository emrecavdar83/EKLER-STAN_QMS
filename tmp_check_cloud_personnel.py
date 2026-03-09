import sys
import os
sys.path.append(os.getcwd())

from database.connection import get_engine
from sqlalchemy import text
import pandas as pd

def check_cloud_personnel():
    # Force cloud connection by setting secrets
    import streamlit as st
    st.secrets = {}
    
    # Try to load secrets from secrets.toml
    try:
        import toml
        with open('.streamlit/secrets.toml', 'r', encoding='utf-8') as f:
            st.secrets = toml.load(f)
    except Exception as e:
        print(f"Uyarı: secrets.toml bulunamadı. {e}")
        
    engine = get_engine()
    print(f"Engine URL: {engine.url}")
    
    if 'sqlite' in str(engine.url):
        print("HATA: Cloud veritabanına bağlanılamadı, hala lokal SQLite çalışıyor.")
        return
        
    with engine.connect() as conn:
        print("\n--- Bulut Veritabanındaki Personeller (Son Eklenenler) ---")
        try:
            query = """
            SELECT p.id, p.ad_soyad, p.kullanici_adi, p.vardiya, p.durum, p.departman_id
            FROM personel p
            ORDER BY p.id DESC LIMIT 20
            """
            
            df = pd.read_sql(text(query), conn)
            print(df.to_string())

        except Exception as e:
            print(f"Hata: {e}")

if __name__ == "__main__":
    check_cloud_personnel()
