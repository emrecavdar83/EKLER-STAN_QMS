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


def add_column(col_name):
    try:
        with engine.begin() as conn:
            print(f"Adding '{col_name}'...")
            conn.execute(text(f"ALTER TABLE personel ADD COLUMN {col_name} TEXT"))
            print(f" -> Added '{col_name}'.")
    except Exception as e:
        print(f" -> '{col_name}' error (maybe exists): {e}")

print("--- ALTERING LIVE DB (Robust) ---")
add_column("bolum")
add_column("sorumlu_bolum")
add_column("kat")
add_column("telefon_no")
add_column("servis_duragi")
print("Done.")
