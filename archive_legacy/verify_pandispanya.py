
import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

SECRETS_PATH = ".streamlit/secrets.toml"
secrets = toml.load(SECRETS_PATH)
DB_URL = secrets["streamlit"]["DB_URL"]
if DB_URL.startswith('"') and DB_URL.endswith('"'):
    DB_URL = DB_URL[1:-1]

engine = create_engine(DB_URL)

with engine.connect() as conn:
    print("--- VERIFICATION: PANDİSPANYA ---")
    
    print("\n--- DEPARTMENTS matching 'PAND' ---")
    try:
        res = conn.execute(text("SELECT * FROM ayarlar_bolumler WHERE bolum_adi LIKE '%PAND%' OR aciklama LIKE '%PAND%'")).fetchall()
        if not res:
            print("No departments found matching PAND")
        for r in res:
            print(f"DEPARTMAN: {r}")
    except Exception as e:
        print(f"Error querying ayarlar_bolumler: {e}")

    print("\n--- LOCATIONS matching 'PAND' ---")
    try:
        # Check for PAND in lokasyon_adi or updated path
        res = conn.execute(text("SELECT * FROM lokasyonlar WHERE ad LIKE '%PAND%' OR sorumlu_departman LIKE '%PAND%'")).fetchall()
        if not res:
            print("No locations found matching PAND")
        for r in res:
            print(f"LOKASYON: {r}")

    except Exception as e:
        print(f"Error querying lokasyonlar: {e}")
