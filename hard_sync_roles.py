
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

local_engine = create_engine('sqlite:///ekleristan_local.db')
live_engine = create_engine(live_url)

print("=== HARD SYNC v3: ROLES AND PERMISSIONS (NO ID) ===")

with local_engine.connect() as loc_conn:
    # Drop ID to avoid PK conflicts, let Postgres generate them
    df_roles = pd.read_sql("SELECT * FROM ayarlar_roller", loc_conn).drop(columns=['id'], errors='ignore')
    df_perms = pd.read_sql("SELECT * FROM ayarlar_yetkiler", loc_conn).drop(columns=['id'], errors='ignore')
    
    if 'aktif' in df_roles.columns:
        df_roles['aktif'] = df_roles['aktif'].apply(lambda x: True if x in [1, True, '1'] else False)

with live_engine.connect() as live_conn:
    print("Deleting Live Permissions...")
    live_conn.execute(text("DELETE FROM ayarlar_yetkiler"))
    live_conn.commit()
    
    print("Deleting Live Roles...")
    live_conn.execute(text("DELETE FROM ayarlar_roller"))
    live_conn.commit()
    
    print("Inserting Local Roles...")
    df_roles.to_sql("ayarlar_roller", live_conn, if_exists='append', index=False)
    live_conn.commit()
    
    print("Inserting Local Permissions...")
    df_perms.to_sql("ayarlar_yetkiler", live_conn, if_exists='append', index=False)
    live_conn.commit()

print("✅ Hard Sync Complete!")
