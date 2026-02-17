from sqlalchemy import create_engine, text
import pandas as pd
import toml
import os

try:
    # Load Secrets
    secrets_path = ".streamlit/secrets.toml"
    if os.path.exists(secrets_path):
        secrets = toml.load(secrets_path)
        if "streamlit" in secrets and "DB_URL" in secrets["streamlit"]:
            db_url = secrets["streamlit"]["DB_URL"]
        else:
            db_url = secrets.get("DB_URL")
    else:
        print("❌ No secrets file found. Cannot check Live DB.")
        exit()

    if db_url.startswith('"'): db_url = db_url[1:-1]
    
    print("Connecting to LIVE DB...")
    engine = create_engine(db_url)
    
    with engine.connect() as conn:
        print("--- LIVE DB USER REPORT ---")
        sql = text("SELECT id, ad_soyad, kullanici_adi, sifre, rol, durum FROM personel WHERE kullanici_adi IN ('emre.cavdar', 'Admin')")
        df = pd.read_sql(sql, conn)
        
        if df.empty:
            print("❌ NO USERS FOUND IN LIVE DB!")
        else:
            print(df.to_string())

except Exception as e:
    print(f"Error: {e}")
