import time
from sqlalchemy import create_engine, text
import os

# Cloud DB URL
DB_URL = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
LOCAL_URL = "sqlite:///ekleristan_local.db"

SQL_FILE = "migrations/20260319_quantum_indexes.sql"

def apply_indexes():
    with open(SQL_FILE, "r") as f:
        sql_commands = f.read().split(";")
    
    # 1. LOCAL SQLITE
    print("Applying to LOCAL SQLite...")
    local_engine = create_engine(LOCAL_URL)
    with local_engine.begin() as conn:
        for cmd in sql_commands:
            if cmd.strip():
                try:
                    conn.execute(text(cmd))
                    print(f"Executed: {cmd[:50]}...")
                except Exception as e:
                    print(f"Error (Local): {e}")

    # 2. CLOUD PG
    print("\nApplying to CLOUD PostgreSQL...")
    cloud_engine = create_engine(DB_URL)
    with cloud_engine.begin() as conn:
        for cmd in sql_commands:
            if cmd.strip():
                try:
                    conn.execute(text(cmd))
                    print(f"Executed: {cmd[:50]}...")
                except Exception as e:
                    print(f"Error (Cloud): {e}")

if __name__ == "__main__":
    apply_indexes()
