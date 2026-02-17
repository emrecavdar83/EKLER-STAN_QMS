import pandas as pd
from sqlalchemy import create_engine

LOCAL_DB_URL = 'sqlite:///ekleristan_local.db'
engine = create_engine(LOCAL_DB_URL)

def inspect_table(table_name):
    print(f"\n--- {table_name} ---")
    try:
        df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
        print(f"Columns: {list(df.columns)}")
        print(f"Row count: {len(df)}")
        if not df.empty:
            print("First 5 rows:")
            print(df.head().to_string())
        else:
            print("Table is empty.")
    except Exception as e:
        print(f"Error querying {table_name}: {e}")

inspect_table('personel_old')
inspect_table('personel')
inspect_table('personnel')
