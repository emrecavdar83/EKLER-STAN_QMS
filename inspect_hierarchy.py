
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
    print("--- DEPARTMENTS CHECK ---")
    target_names = ['BOMBA', 'PROFİTEROL', 'RULO PASTA', 'OKUL PROJESİ', 'ÜRETİM', 'KEK', 'PANDİSPANYA']
    # Also check if OKUL PROJESİ is valid or maybe it has a different name
    query_names = "', '".join(target_names)
    
    # 1. Check exact matches
    print("\nExact Matches:")
    res = conn.execute(text(f"SELECT * FROM ayarlar_bolumler WHERE bolum_adi IN ('{query_names}')")).fetchall()
    for r in res:
        print(r)
        
    # 2. Check like matches for OKUL
    print("\nLike 'OKUL':")
    res = conn.execute(text("SELECT * FROM ayarlar_bolumler WHERE bolum_adi LIKE '%OKUL%'")).fetchall()
    for r in res:
        print(r)

    print("\n--- LOCATIONS CHECK ---")
    # Check locations for these names
    res = conn.execute(text(f"SELECT * FROM lokasyonlar WHERE ad IN ('{query_names}') OR ad LIKE '%OKUL%' OR sorumlu_departman LIKE '%OKUL%'")).fetchall()
    for r in res:
        print(r)
