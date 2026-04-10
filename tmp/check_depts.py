import sys
import os
from sqlalchemy import text

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_engine

def check_db():
    engine = get_engine()
    with engine.connect() as conn:
        print("--- qms_departmanlar columns ---")
        # Check columns using PRAGMA for SQLite or info schema for PG
        is_pg = engine.dialect.name == 'postgresql'
        if is_pg:
            res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'qms_departmanlar'"))
        else:
            res = conn.execute(text("PRAGMA table_info(qms_departmanlar)"))
        
        cols = [r[0] if is_pg else r[1] for r in res]
        print(f"Columns: {cols}")
        
        if "durum" in cols:
            print("✅ 'durum' column exists.")
            data = conn.execute(text("SELECT id, ad, durum FROM qms_departmanlar LIMIT 5")).fetchall()
            print("Sample Data:")
            for row in data:
                print(row)
        else:
            print("❌ 'durum' column MISSING.")

if __name__ == "__main__":
    try:
        check_db()
    except Exception as e:
        print(f"Error: {e}")
