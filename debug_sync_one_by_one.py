
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

with local_engine.connect() as loc_conn:
    df_perms = pd.read_sql("SELECT rol_adi, modul_adi, erisim_turu FROM ayarlar_yetkiler", loc_conn)

with live_engine.connect() as live_conn:
    print("Clearing...")
    live_conn.execute(text("DELETE FROM ayarlar_yetkiler"))
    live_conn.commit()
    
    print(f"Inserting {len(df_perms)} rows one by one...")
    for idx, row in df_perms.iterrows():
        try:
            row_df = pd.DataFrame([row])
            row_df.to_sql("ayarlar_yetkiler", live_conn, if_exists='append', index=False)
            # live_conn.commit() # optional, but let's be sure
        except Exception as e:
            print(f"FAILED on row {idx}: {row.to_dict()}")
            print(f"Error: {e}")
            break
            
print("Sync test finished.")
