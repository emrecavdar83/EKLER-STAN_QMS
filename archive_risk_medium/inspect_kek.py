
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
    print("--- TABLES ---")
    tables = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
    # for t in tables:
    #     print(t[0])
    
    print("\n--- DEPARTMENTS matching 'KEK' ---")
    try:
        res = conn.execute(text("SELECT * FROM ayarlar_bolumler WHERE bolum_adi LIKE '%KEK%'")).fetchall()
        for r in res:
            print(f"AYARLAR_BOLUMLER: {r}")
    except Exception as e:
        print(f"Error querying ayarlar_bolumler: {e}")

    print("\n--- LOCATIONS (lokasyonlar) matching 'KEK' ---")
    try:
        cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'lokasyonlar'")).fetchall()
        print(f"Columns in lokasyonlar: {[c[0] for c in cols]}")
        
        # Check for KEK in lokasyon_adi (guessing column name based on checking all cols)
        res = conn.execute(text("SELECT * FROM lokasyonlar")).fetchall()
        # print(f"Total rows in lokasyonlar: {len(res)}")
        for r in res:
            if "KEK" in str(r):
                print(f"Found in lokasyonlar: {r}")

    except Exception as e:
        print(f"Error querying lokasyonlar: {e}")

    print("\n--- GMP LOCATIONS (gmp_lokasyonlar) matching 'KEK' ---")
    try:
        cols = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'gmp_lokasyonlar'")).fetchall()
        print(f"Columns in gmp_lokasyonlar: {[c[0] for c in cols]}")
        
        res = conn.execute(text("SELECT * FROM gmp_lokasyonlar")).fetchall()
        for r in res:
            if "KEK" in str(r):
                print(f"Found in gmp_lokasyonlar: {r}")

    except Exception as e:
        print(f"Error querying gmp_lokasyonlar: {e}")
