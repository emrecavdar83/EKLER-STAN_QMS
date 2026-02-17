
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
    print("--- UPDATING HIERARCHY: BOMBA/PROFİTEROL -> OKUL PROJESİ ---")
    
    # 1. Update ayarlar_bolumler (Departments)
    # OKUL PROJESİ ID = 21
    # BOMBA ID = 10
    # PROFİTEROL ID = 9
    # Column for parent: 'ust_id' (Need to be sure, will assume 'ust_id' based on previous context, but if query above shows different I will adjust)
    # The columns from inspection were likely: id, bolum_adi, aciklama, aktif, ?, ?, ust_id
    
    # I'll rely on the column check in parallel step, but to be robust I'll try to find the parent column name if I can't wait.
    # Actually, I am generating this file in parallel to the check. I'll read the check output before running this, or I'll just check columns inside this script.
    
    print("Checking columns...")
    cols_query = text("SELECT column_name FROM information_schema.columns WHERE table_name = 'ayarlar_bolumler'")
    cols = [r[0] for r in conn.execute(cols_query).fetchall()]
    print(f"Columns: {cols}")
    
    # Based on failure output, the column is 'ana_departman_id'
    parent_col = 'ana_departman_id'
    if parent_col not in cols:
        # Fallback to check if ust_id exists just in case
        if 'ust_id' in cols:
            parent_col = 'ust_id'
        else:
            print(f"CRITICAL: Could not find parent column 'ana_departman_id' in {cols}. Aborting.")
            exit(1)
        
    print(f"Using parent column: {parent_col}")

    try:
        # Update BOMBA (10) -> Parent 21
        conn.execute(text(f"UPDATE ayarlar_bolumler SET {parent_col} = 21 WHERE id = 10"))
        print("Updated BOMBA parent to 21.")
        
        # Update PROFİTEROL (9) -> Parent 21
        conn.execute(text(f"UPDATE ayarlar_bolumler SET {parent_col} = 21 WHERE id = 9"))
        print("Updated PROFİTEROL parent to 21.")
        
    except Exception as e:
        print(f"Error updating departments: {e}")
        
    # 2. Update lokasyonlar (Locations)
    print("\nUpdating lokasyonlar paths...")
    # Current: YÖNETİM > ÜRETİM > BOMBA
    # Target: YÖNETİM > ÜRETİM > OKUL PROJESİ > BOMBA
    
    try:
        # Update BOMBA location path
        # Using REPLACE to inject 'OKUL PROJESİ > ' before 'BOMBA' and 'PROFİTEROL' in the path seems risky if run multiple times.
        # Better to Set straight if we match the exact string, or use regex.
        # Let's try to match the specific current known path.
        
        # BOMBA
        conn.execute(text("UPDATE lokasyonlar SET sorumlu_departman = REPLACE(sorumlu_departman, 'ÜRETİM > BOMBA', 'ÜRETİM > OKUL PROJESİ > BOMBA') WHERE sorumlu_departman LIKE '%ÜRETİM > BOMBA%'"))
        
        # PROFİTEROL
        conn.execute(text("UPDATE lokasyonlar SET sorumlu_departman = REPLACE(sorumlu_departman, 'ÜRETİM > PROFİTEROL', 'ÜRETİM > OKUL PROJESİ > PROFİTEROL') WHERE sorumlu_departman LIKE '%ÜRETİM > PROFİTEROL%'"))
        
        print("Updated lokasyonlar paths.")
    except Exception as e:
        print(f"Error updating lokasyonlar: {e}")

    try:
        conn.commit()
        print("Changes committed.")
    except:
        pass

# Verify
with engine.connect() as conn:
    print("\n--- NEW HIERARCHY ---")
    res = conn.execute(text(f"SELECT * FROM ayarlar_bolumler WHERE id IN (9, 10, 21)")).fetchall()
    for r in res:
        print(r)
