
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
    print("\n--- Department breakdown for Gündüz Vardiyası (Live) ---")
    df = pd.read_sql("""
        SELECT d.bolum_adi, p.rol, p.durum, COUNT(*) as count 
        FROM personel p
        LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
        WHERE UPPER(p.vardiya) = 'GÜNDÜZ VARDİYASI'
        AND UPPER(p.durum) = 'AKTİF'
        GROUP BY d.bolum_adi, p.rol, p.durum
        ORDER BY d.bolum_adi
    """, conn)
    print(df.to_string())
