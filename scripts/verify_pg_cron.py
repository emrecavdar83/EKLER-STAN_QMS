import os, sys
sys.path.append(os.getcwd())
import pandas as pd
from sqlalchemy import text
from database.connection import get_engine

def check_pg_cron():
    print("Checking pg_cron status...")
    engine = get_engine()
    if engine.dialect.name != 'postgresql':
        print("PG_CRON Status: N/A (SQLite/Local)")
        return
    
    try:
        with engine.connect() as conn:
            sql = text("SELECT 1 FROM pg_extension WHERE extname = 'pg_cron'")
            res = conn.execute(sql).scalar()
            if res:
                print("PG_CRON Status: ACTIVE")
            else:
                print("PG_CRON Status: NOT FOUND")
    except Exception as e:
        print(f"PG_CRON Status: ERROR ({e})")

if __name__ == "__main__":
    check_pg_cron()
