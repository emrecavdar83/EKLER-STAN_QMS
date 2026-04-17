from sqlalchemy import text
import sys
import os

# PYTHONPATH ayarı
sys.path.append(os.getcwd())

from database.connection import get_engine

def verify():
    print("Verifying System State...")
    try:
        engine = get_engine()
        print("OK: Database connection successful.")
        
        with engine.connect() as conn:
            # 1. Check if dead tables are really gone
            dead_tables = ["flow_definitions", "personnel_tasks", "sistem_modulleri"]
            for tbl in dead_tables:
                res = conn.execute(text(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{tbl}' AND table_schema = 'public'")).fetchone()
                if res and res[0] == 0:
                    print(f"OK: Dead table '{tbl}' is gone.")
                else:
                    print(f"WARNING: Dead table '{tbl}' still exists or check failed.")
            
            # 2. Check core tables
            core_tables = ["ayarlar_kullanicilar", "ayarlar_moduller", "sistem_loglari"]
            for tbl in core_tables:
                try:
                    conn.execute(text(f"SELECT 1 FROM {tbl} LIMIT 1"))
                    print(f"OK: Core table '{tbl}' exists and accessible.")
                except Exception as e:
                    print(f"ERROR: Core table '{tbl}' error: {e}")
                    
            # 3. Check standardized columns
            try:
                conn.execute(text("SELECT durum FROM ayarlar_moduller LIMIT 1"))
                print("OK: 'durum' column exists in ayarlar_moduller.")
            except:
                print("WARNING: 'durum' column missing in ayarlar_moduller.")

        print("Verification Complete.")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    verify()
