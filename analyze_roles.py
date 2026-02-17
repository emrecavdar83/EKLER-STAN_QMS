
import pandas as pd
from sqlalchemy import create_engine, text
import os
import toml

# Get live DB URL
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

local_engine = create_engine('sqlite:///ekleristan_local.db')
live_engine = create_engine(live_url) if live_url else None

print("=== ROLE ANALYSIS (LOCAL vs LIVE) ===")

with local_engine.connect() as conn:
    df_local = pd.read_sql("SELECT id, rol_adi FROM ayarlar_roller", conn)
    print("\nLOCAL ROLES:")
    for _, row in df_local.iterrows():
        print(f"ID: {row['id']}, Name: '{row['rol_adi']}', Len: {len(row['rol_adi'])}")

if live_engine:
    with live_engine.connect() as conn:
        df_live = pd.read_sql("SELECT id, rol_adi FROM ayarlar_roller", conn)
        print("\nLIVE ROLES:")
        for _, row in df_live.iterrows():
            print(f"ID: {row['id']}, Name: '{row['rol_adi']}', Len: {len(row['rol_adi'])}")
else:
    print("\nLive DB URL not found!")
