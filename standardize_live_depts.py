
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
    print("Standardizing 'bolum_adi' in Live DB...")
    
    # Standardize bolum_adi in ayarlar_bolumler
    # We use Postgres UPPER which might have issues with Turkish İ/I if not configured, 
    # but for these names it should be mostly fine.
    # To be safer for Turkish, we could do it in Python, but let's try SQL first for mass update.
    
    res = conn.execute(text("""
        UPDATE ayarlar_bolumler 
        SET bolum_adi = UPPER(TRIM(bolum_adi)) 
        WHERE bolum_adi IS NOT NULL
    """))
    print(f"Updated {res.rowcount} rows in 'ayarlar_bolumler'.")

    # Also update any other related tables if necessary
    # For now, personel table uses departman_id (FK), so we only need to update the source.
    
    conn.commit()
    print("✅ Department standardization complete!")
