import toml
from sqlalchemy import create_engine, text
import os

try:
    secrets = toml.load(".streamlit/secrets.toml")
    url = secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")
    if url.startswith('"') and url.endswith('"'): url = url[1:-1]
    
    engine = create_engine(url)
    with engine.begin() as conn:
        with open('migrations/20260328_100000_gunluk_gorev_ve_akis_init.sql', 'r', encoding='utf-8') as f:
            sql_text = f.read()
            # Split by semicolons for executing multiple statements properly in some SQL drivers
            statements = sql_text.split(';')
            for stmt in statements:
                if stmt.strip():
                    conn.execute(text(stmt))
        print("Migration 100000 LIVE'a islendi.")
        
        with open('migrations/20260328_130000_cloud_tablo_temizligi.sql', 'r', encoding='utf-8') as f:
            sql_text = f.read()
            statements = sql_text.split(';')
            for stmt in statements:
                if stmt.strip():
                    conn.execute(text(stmt))
        print("Migration 130000 (Temizlik) LIVE'a islendi.")
except Exception as e:
    print(f"Hata: {e}")
