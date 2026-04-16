
import os
import toml
import sqlalchemy
from sqlalchemy import text
import sys

# Set encoding for console output
sys.stdout.reconfigure(encoding='utf-8')

try:
    s = toml.load('.streamlit/secrets.toml')
    db_url = s.get("DB_URL") or s.get("streamlit", {}).get("DB_URL")
    if not db_url:
        print("No DB_URL found in secrets.toml")
        sys.exit(1)
        
    engine = sqlalchemy.create_engine(db_url)
    with engine.connect() as conn:
        print("--- Column Info for sistem_parametreleri ---")
        res = conn.execute(text("SELECT column_name, data_type, character_maximum_length FROM information_schema.columns WHERE table_name = 'sistem_parametreleri'")).fetchall()
        for r in res:
            print(r)
            
        print("\n--- Check RLS status for urun_kpi_kontrol ---")
        res_rls = conn.execute(text("SELECT relname, relrowsecurity FROM pg_class JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace WHERE relname = 'urun_kpi_kontrol' AND nspname = 'public'")).fetchone()
        print(f"Table: {res_rls[0]}, RLS Enabled: {res_rls[1]}")
        
except Exception as e:
    print(f"Error: {e}")
