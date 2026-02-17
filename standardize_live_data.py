
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
    print("Standardizing 'durum' and 'vardiya' columns to UPPERCASE in Live DB...")
    
    # Standardize durum
    res_durum = conn.execute(text("""
        UPDATE personel 
        SET durum = UPPER(TRIM(durum)) 
        WHERE durum IS NOT NULL
    """))
    print(f"Updated {res_durum.rowcount} rows for 'durum'.")
    
    # Standardize vardiya
    res_vardiya = conn.execute(text("""
        UPDATE personel 
        SET vardiya = UPPER(TRIM(vardiya)) 
        WHERE vardiya IS NOT NULL
    """))
    print(f"Updated {res_vardiya.rowcount} rows for 'vardiya'.")
    
    # Standardize rol
    res_rol = conn.execute(text("""
        UPDATE personel 
        SET rol = UPPER(TRIM(rol)) 
        WHERE rol IS NOT NULL
    """))
    print(f"Updated {res_rol.rowcount} rows for 'rol'.")

    conn.commit()
    print("✅ Standardization complete!")
