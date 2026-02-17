
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
    print("\n--- Role and Status Breakdown in Gündüz Vardiyası ---")
    df = pd.read_sql("""
        SELECT rol, durum, COUNT(*) as count 
        FROM personel 
        WHERE UPPER(vardiya) = 'GÜNDÜZ VARDİYASI' 
        GROUP BY rol, durum
    """, conn)
    print(df)
