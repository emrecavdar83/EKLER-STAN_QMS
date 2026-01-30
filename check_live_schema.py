import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

SECRETS_PATH = os.path.join(os.path.dirname(__file__), ".streamlit", "secrets.toml")
secrets = toml.load(SECRETS_PATH)
if "streamlit" in secrets and "DB_URL" in secrets["streamlit"]:
    LIVE_DB_URL = secrets["streamlit"]["DB_URL"]
else:
    LIVE_DB_URL = secrets["DB_URL"]
if LIVE_DB_URL.startswith('"') and LIVE_DB_URL.endswith('"'):
    LIVE_DB_URL = LIVE_DB_URL[1:-1]

engine = create_engine(LIVE_DB_URL)

with engine.connect() as conn:
    print("--- LIVE PERSONEL COLUMNS ---")
    # For Postgres
    res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'personel'"))
    for row in res:
        print(f"- {row[0]}")
