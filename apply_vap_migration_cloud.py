import sqlalchemy
from sqlalchemy import text

# Supabase PostgreSQL URL
DB_URL = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

def run_fix():
    print("Connecting to Cloud DB...")
    try:
        engine = sqlalchemy.create_engine(DB_URL)
        with engine.begin() as conn:
            print("Adding missing columns to 'personel_vardiya_programi'...")
            
            # v5.8.5: Missing Columns Fix
            commands = [
                "ALTER TABLE personel_vardiya_programi ADD COLUMN IF NOT EXISTS onay_durumu TEXT DEFAULT 'ONAYLANDI'",
                "ALTER TABLE personel_vardiya_programi ADD COLUMN IF NOT EXISTS onaylayan_id INTEGER",
                "ALTER TABLE personel_vardiya_programi ADD COLUMN IF NOT EXISTS onay_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ]
            
            for cmd in commands:
                try:
                    conn.execute(text(cmd))
                    print(f"SUCCESS: {cmd}")
                except Exception as e:
                    print(f"SKIPPED/ERROR: {cmd} -> {e}")
                    
            print("\nUpdating all existing records to 'ONAYLANDI'...")
            conn.execute(text("UPDATE personel_vardiya_programi SET onay_durumu = 'ONAYLANDI' WHERE onay_durumu IS NULL"))
            
        print("\n--- CLOUD MIGRATION COMPLETED SUCCESSFULLY ---")
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")

if __name__ == "__main__":
    run_fix()
