
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
    print("\n--- Try to get v_organizasyon_semasi definition ---")
    try:
        # For Postgres (Supabase uses Postgres)
        res = conn.execute(text("SELECT definition FROM pg_views WHERE viewname = 'v_organizasyon_semasi'")).fetchone()
        if res:
            print(res[0])
        else:
            print("View definition not found in pg_views.")
    except Exception as e:
        print(f"Error fetching view definition: {e}")

    print("\n--- Sample data from v_organizasyon_semasi ---")
    try:
        df = pd.read_sql("SELECT * FROM v_organizasyon_semasi LIMIT 10", conn)
        print(df)
    except Exception as e:
        print(f"Error fetching data from view: {e}")
