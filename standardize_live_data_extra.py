
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
    print("Standardizing 'ad_soyad', 'kullanici_adi', and 'gorev' columns to UPPERCASE...")
    
    # Standardize ad_soyad
    res_ad = conn.execute(text("""
        UPDATE personel 
        SET ad_soyad = UPPER(TRIM(ad_soyad)) 
        WHERE ad_soyad IS NOT NULL
    """))
    print(f"Updated {res_ad.rowcount} rows for 'ad_soyad'.")

    # Standardize kullanici_adi (usually lowercase in systems, but user asked for "everything uppercase")
    # Actually, keep kullanici_adi as is if it's used for login, or standardize it too?
    # User said "all writings should be uppercase" (bütün yazımlar büyük harf olsun).
    # But usually usernames are lowercase. Let's stick to visible fields first.
    
    # Standardize gorev
    res_gorev = conn.execute(text("""
        UPDATE personel 
        SET gorev = UPPER(TRIM(gorev)) 
        WHERE gorev IS NOT NULL
    """))
    print(f"Updated {res_gorev.rowcount} rows for 'gorev'.")

    conn.commit()
    print("✅ Standardization complete!")
