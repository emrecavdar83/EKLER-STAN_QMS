
import pandas as pd
from sqlalchemy import create_engine, text
import os
import toml

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
    print("Deleting...")
    conn.execute(text("DELETE FROM ayarlar_yetkiler"))
    conn.commit()
    
    res = conn.execute(text("SELECT COUNT(*) FROM ayarlar_yetkiler")).fetchone()
    print(f"Count after delete: {res[0]}")
    
    if res[0] > 0:
        print("!!! DELETE FAILED OR DATA REAPPEARED !!!")
