
from sqlalchemy import create_engine, text
import pandas as pd

def get_engine():
    db_url = "postgresql://postgres.bogritpjqxcdmodxxfhv:%409083%26tprk_E@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"
    return create_engine(db_url)

engine = get_engine()

def inspect_schema():
    try:
        with engine.connect() as conn:
            print("--- Table Columns and Types ---")
            for table in ['soguk_odalar', 'sicaklik_olcumleri', 'olcum_plani']:
                df = pd.read_sql(text(f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = '{table}'"), conn)
                print(f"\nTable: {table}")
                print(df.to_string())
            
            print("\n--- Database Timezone ---")
            tz = conn.execute(text("SHOW TIMEZONE")).scalar()
            print(f"Postgres Timezone: {tz}")
            
    except Exception as e:
        print(f"Inspection failed: {e}")

if __name__ == "__main__":
    inspect_schema()
