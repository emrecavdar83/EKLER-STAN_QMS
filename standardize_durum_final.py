
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
    print("Standardizing 'durum' values in Live DB...")
    
    # Check current status values again
    df = pd.read_sql("SELECT DISTINCT durum FROM personel", conn)
    print("Current durum values:", df['durum'].tolist())
    
    # Update to AKTİF and PASİF
    res = conn.execute(text("""
        UPDATE personel 
        SET durum = CASE 
            WHEN UPPER(TRIM(durum)) IN ('AKTİF', 'AKTIF', 'ACTIVE', 'TRUE', '1') THEN 'AKTİF'
            WHEN UPPER(TRIM(durum)) IN ('PASİF', 'PASIF', 'PASSIVE', 'FALSE', '0') THEN 'PASİF'
            ELSE UPPER(TRIM(durum))
        END
        WHERE durum IS NOT NULL
    """))
    print(f"Standardized {res.rowcount} rows.")

    conn.commit()
    
    # Final check
    df_after = pd.read_sql("SELECT DISTINCT durum FROM personel", conn)
    print("Final durum values:", df_after['durum'].tolist())

    print("✅ Standardization double-check complete!")
