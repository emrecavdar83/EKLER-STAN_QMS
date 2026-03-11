
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime

def get_engine():
    db_url = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
    return create_engine(db_url)

engine = get_engine()

def test_reading():
    try:
        with engine.connect() as conn:
            # Insert a known value
            now_label = datetime(2026, 3, 10, 10, 0, 0) # 10:00 AM
            print(f"Original Label: {now_label} (Type: {type(now_label)})")
            
            # Read a few recent records
            df = pd.read_sql(text("SELECT olcum_zamani FROM sicaklik_olcumleri ORDER BY id DESC LIMIT 5"), conn)
            print("\nRead Records:")
            for idx, row in df.iterrows():
                val = row['olcum_zamani']
                print(f"Index {idx}: Value: {val}, Type: {type(val)}, TZInfo: {val.tzinfo if hasattr(val, 'tzinfo') else 'None'}")
                
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    test_reading()
