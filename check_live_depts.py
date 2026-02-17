
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

live_engine = create_engine(live_url)

with live_engine.connect() as conn:
    print("\n--- Personnel Department ID and Name ---")
    df = pd.read_sql("""
        SELECT p.ad_soyad, p.rol, p.departman_id, d.bolum_adi, p.durum, p.vardiya
        FROM personel p
        LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
        WHERE UPPER(p.vardiya) = 'GÜNDÜZ VARDİYASI'
        AND UPPER(p.durum) = 'AKTİF'
        LIMIT 50
    """, conn)
    print(df)
    
    print("\n--- Personnel with NO Department in Gündüz Vardiyası ---")
    df_no_dept = pd.read_sql("""
        SELECT COUNT(*) as count 
        FROM personel 
        WHERE departman_id IS NULL OR departman_id = 0
        AND UPPER(vardiya) = 'GÜNDÜZ VARDİYASI'
    """, conn)
    print(df_no_dept)
