import sqlalchemy
from sqlalchemy import text
import streamlit as st

# Supabase PostgreSQL URL (Secrets'tan alınıyor)
DB_URL = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
LOCAL_URL = "sqlite:///ekleristan_local.db"

def purge_tables():
    tables_to_drop = [
        "flow_definitions", "flow_nodes", "flow_edges", 
        "flow_bypass_logs", "personnel_tasks"
    ]
    
    # 1. CLOUD PURGE
    print("Connecting to CLOUD DB (Supabase)...")
    try:
        engine = sqlalchemy.create_engine(DB_URL)
        with engine.begin() as conn:
            for table in tables_to_drop:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    print(f"SUCCESS: {table} dropped from Cloud.")
                except Exception as e:
                    print(f"ERROR: {table} not dropped -> {e}")
    except Exception as e:
        print(f"Cloud Connection Failed: {e}")

    # 2. LOCAL PURGE
    print("\nConnecting to LOCAL DB (SQLite)...")
    try:
        engine_local = sqlalchemy.create_engine(LOCAL_URL)
        with engine_local.begin() as conn:
            for table in tables_to_drop:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                    print(f"SUCCESS: {table} dropped from Local.")
                except Exception as e:
                    print(f"ERROR: {table} not dropped -> {e}")
    except Exception as e:
        print(f"Local Connection Failed: {e}")

    print("\n--- DATABASE PURGE COMPLETED ---")

if __name__ == "__main__":
    purge_tables()
