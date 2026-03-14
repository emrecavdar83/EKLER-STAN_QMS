from sqlalchemy import create_engine, text
import pandas as pd

# Cloud DB URL from secrets.toml (mocked or hardcoded for this check)
CLOUD_URL = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

def check_cloud_shifts():
    engine = create_engine(CLOUD_URL)
    with engine.connect() as conn:
        print("--- TODAY'S SHIFTS (CLOUD) ---")
        try:
            sql = "SELECT id, tarih, makina_no, operator_adi, durum FROM map_vardiya WHERE tarih = (CURRENT_DATE AT TIME ZONE 'Europe/Istanbul')::text"
            df = pd.read_sql(text(sql), conn)
            print(df)
            
            print("\n--- ALL ACTIVE SHIFTS (CLOUD) ---")
            df_active = pd.read_sql(text("SELECT * FROM map_vardiya WHERE durum='ACIK'"), conn)
            print(df_active)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_cloud_shifts()
