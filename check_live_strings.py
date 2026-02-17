
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
    print("\n--- Exact Vardiya Strings (Live) ---")
    df = pd.read_sql("SELECT DISTINCT vardiya, '|' || vardiya || '|' as piped FROM personel", conn)
    print(df)
    
    print("\n--- Exact Durum Strings (Live) ---")
    df_d = pd.read_sql("SELECT DISTINCT durum, '|' || durum || '|' as piped FROM personel", conn)
    print(df_d)
