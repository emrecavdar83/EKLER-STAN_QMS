
from sqlalchemy import create_engine, text
import toml
import os

def fix():
    print("Starting Cloud Fix V2...")
    secrets = toml.load(".streamlit/secrets.toml")
    db_url = secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")
    if not db_url:
        print("No DB_URL found.")
        return
    
    engine = create_engine(db_url)
    
    migrations = [
        "ALTER TABLE personel ADD COLUMN operasyonel_bolum_id INTEGER",
        "ALTER TABLE personel ADD COLUMN ikincil_yonetici_id INTEGER",
        "ALTER TABLE ayarlar_bolumler ADD COLUMN aciklama TEXT",
        "ALTER TABLE ayarlar_bolumler ADD COLUMN ana_departman_id INTEGER",
        "ALTER TABLE ayarlar_moduller ADD COLUMN sira_no INTEGER"
    ]
    
    for sql in migrations:
        try:
            # Use a fresh connection for each migration to avoid transaction abort lock-up
            with engine.connect() as conn:
                # Set autocommit for the connection
                conn.execution_options(isolation_level="AUTOCOMMIT").execute(text(sql))
                print(f"SUCCESS: {sql}")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print(f"SKIPPED (Already exists): {sql}")
            else:
                print(f"FAILED: {sql} | Error: {e}")

    print("Verifying critical columns...")
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'personel' AND column_name = 'operasyonel_bolum_id'")).fetchone()
            if res:
                print("Verification: 'operasyonel_bolum_id' column EXISTS.")
            else:
                print("Verification: 'operasyonel_bolum_id' column MISSING.")
    except Exception as e:
        print(f"Verification error: {e}")

if __name__ == "__main__":
    fix()
