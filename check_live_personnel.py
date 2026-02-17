
import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

def get_live_url():
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        if "streamlit" in secrets and "DB_URL" in secrets["streamlit"]:
            return secrets["streamlit"]["DB_URL"]
        elif "DB_URL" in secrets:
            return secrets["DB_URL"]
    return None

live_url = get_live_url()
if live_url and live_url.startswith('"'): live_url = live_url[1:-1]

if not live_url:
    print("Live URL not found!")
    exit(1)

live_engine = create_engine(live_url)

print("--- Live Personel Data Summary ---")
with live_engine.connect() as conn:
    print("\n--- Shift Distribution ---")
    df_v = pd.read_sql("SELECT vardiya, COUNT(*) as count FROM personel GROUP BY vardiya", conn)
    print(df_v)
    
    print("\n--- Status Distribution ---")
    df_s = pd.read_sql("SELECT durum, COUNT(*) as count FROM personel GROUP BY durum", conn)
    print(df_s)

    print("\n--- Gündüz Vardiyası Personnel Sample ---")
    # Shift names are usually uppercase in the logic but let's see what's in DB
    df_g = pd.read_sql("""
        SELECT ad_soyad, rol, vardiya, durum 
        FROM personel 
        WHERE UPPER(vardiya) LIKE '%GÜNDÜZ%' 
        LIMIT 20
    """, conn)
    print(df_g)

    print("\n--- Gündüz Vardiyası Role Count ---")
    df_rc = pd.read_sql("""
        SELECT rol, COUNT(*) as count 
        FROM personel 
        WHERE UPPER(vardiya) LIKE '%GÜNDÜZ%' 
        GROUP BY rol
    """, conn)
    print(df_rc)

    print("\n--- Regular Personnel in Gündüz Vardiyası? ---")
    df_reg = pd.read_sql("""
        SELECT ad_soyad, rol, vardiya, durum 
        FROM personel 
        WHERE UPPER(vardiya) LIKE '%GÜNDÜZ%' 
        AND UPPER(rol) NOT IN ('ADMIN', 'YÖNETİM', 'BÖLÜM SORUMLUSU', 'VARDIYA AMIRI')
        LIMIT 10
    """, conn)
    print(df_reg)

