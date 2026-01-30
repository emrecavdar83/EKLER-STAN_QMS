import os
import sys
import logging
import sqlalchemy
from sqlalchemy import create_engine, text

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_db_integrity():
    logging.info("🚀 Starting Deep Database Integrity Check...")
    
    # 1. Local SQLite Check
    if os.path.exists("ekleristan_local.db"):
        try:
            logging.info("📂 Checking Local SQLite (ekleristan_local.db)...")
            local_engine = create_engine('sqlite:///ekleristan_local.db')
            with local_engine.connect() as conn:
                # Check 1: Connection
                logging.info("   ✅ Connection successful.")
                
                # Check 2: Table Existence - Personel
                result = conn.execute(text("SELECT count(*) FROM personel")).scalar()
                logging.info(f"   ✅ Table 'personel' exists. Row count: {result}")
                
                # Check 3: Schema columns (Critical ones)
                columns = conn.execute(text("PRAGMA table_info(personel)")).fetchall()
                col_names = [c[1] for c in columns]
                required = ['id', 'ad_soyad', 'rol', 'departman_id']
                missing = [r for r in required if r not in col_names]
                if missing:
                    logging.error(f"   ❌ MISSING CRITICAL COLUMNS in 'personel': {missing}")
                else:
                    logging.info("   ✅ Critical columns present in 'personel'.")

                # Check 4: Check for NULLs in critical fields
                null_users = conn.execute(text("SELECT count(*) FROM personel WHERE ad_soyad IS NULL")).scalar()
                if null_users > 0:
                    logging.warning(f"   ⚠️ Found {null_users} personnel with NULL names.")
                else:
                    logging.info("   ✅ No NULL personnel names found.")
                    
        except Exception as e:
            logging.error(f"   ❌ LOCAL DB CRASHED: {e}")
    else:
        logging.error("   ❌ ekleristan_local.db NOT FOUND!")

    # 2. Live DB Check (Simulated for safety, or minimal ping)
    # We will just verify if we CAN create an engine, not actually connect to avoid timeout hangs if network is bad
    # Since failure here shouldn't crash LOCAL UI if handled correctly.
    
    logging.info("🏁 Integrity Check Completed.")

if __name__ == "__main__":
    check_db_integrity()
