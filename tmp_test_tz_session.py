
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime

def get_engine():
    db_url = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
    return create_engine(db_url)

engine = get_engine()

def test_session_tz():
    try:
        with engine.connect() as conn:
            conn.execute(text("SET TIMEZONE='Europe/Istanbul'"))
            print("Session TZ set to Europe/Istanbul")
            
            # Read a few recent records
            df = pd.read_sql(text("SELECT id, olcum_zamani FROM sicaklik_olcumleri ORDER BY id DESC LIMIT 5"), conn)
            print("\nRead Records (after SET TIMEZONE):")
            for idx, row in df.iterrows():
                val = row['olcum_zamani']
                print(f"ID {row['id']}: Value: {val}, Type: {type(val)}")
                
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_session_tz()
