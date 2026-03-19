
import streamlit as st
from database.connection import get_engine, auto_migrate_schema
from sqlalchemy import text
import sys
import os

# Set project path
sys.path.append('c:/Projeler/S_program/EKLERİSTAN_QMS')

def fix_cloud():
    print("Cloud Schema Fix Initiated...")
    engine = get_engine()
    
    # Check if we are connected to cloud
    if 'sqlite' in str(engine.url):
        print("Local SQLite detected. Attempting to load cloud secrets...")
        # Force load secrets manually if needed, but get_engine should have handled it if DB_URL env is set
        # OR we can pass the URL directly from secrets.toml if running locally
        import toml
        secrets = toml.load(".streamlit/secrets.toml")
        db_url = secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")
        if db_url:
            from sqlalchemy import create_engine
            engine = create_engine(db_url)
            print("Connected to Cloud Database (Supabase/Postgres)")
        else:
            print("Could not find Cloud DB URL.")
            return

    try:
        auto_migrate_schema(engine)
        print("Cloud Schema Migration Completed.")
        
        # Verify specific columns
        with engine.connect() as conn:
            res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'personel' AND column_name = 'operasyonel_bolum_id'")).fetchone()
            if res:
                print("Verification: 'operasyonel_bolum_id' column EXISTS.")
            else:
                print("Verification: 'operasyonel_bolum_id' column STILL MISSING.")
    except Exception as e:
        print(f"Error during cloud fix: {e}")

if __name__ == "__main__":
    fix_cloud()
