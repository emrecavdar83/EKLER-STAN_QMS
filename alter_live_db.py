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

with engine.begin() as conn:
    print("--- ALTERING LIVE DB ---")
    
    # 1. bolum
    try:
        print("Adding 'bolum'...")
        conn.execute(text("ALTER TABLE personel ADD COLUMN bolum TEXT"))
        print(" -> Added 'bolum'.")
    except Exception as e:
        print(f" -> 'bolum' error (maybe exists): {e}")

    # 2. sorumlu_bolum
    try:
        print("Adding 'sorumlu_bolum'...")
        conn.execute(text("ALTER TABLE personel ADD COLUMN sorumlu_bolum TEXT"))
        print(" -> Added 'sorumlu_bolum'.")
    except Exception as e:
        print(f" -> 'sorumlu_bolum' error (maybe exists): {e}")

    # 3. kat
    try:
        print("Adding 'kat'...")
        conn.execute(text("ALTER TABLE personel ADD COLUMN kat TEXT"))
        print(" -> Added 'kat'.")
    except Exception as e:
        print(f" -> 'kat' error (maybe exists): {e}")

    print("Done.")
