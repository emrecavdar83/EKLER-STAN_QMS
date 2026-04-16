import pandas as pd
from sqlalchemy import create_engine, text
import os

def test_pd_read_sql():
    # Local SQLite DB for test
    db_path = 'ekleristan_local.db'
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return
    
    engine = create_engine(f'sqlite:///{db_path}')
    
    print(f"Pandas version: {pd.__version__}")
    try:
        import sqlalchemy
        print(f"SQLAlchemy version: {sqlalchemy.__version__}")
    except:
        pass

    print("\nAttempting pd.read_sql WITHOUT monkey patch...")
    try:
        # Simple query
        df = pd.read_sql(text("SELECT 1 as test"), engine.connect())
        print("SUCCESS: pd.read_sql worked!")
        print(df)
    except Exception as e:
        print(f"FAILURE: pd.read_sql failed with error: {e}")

if __name__ == "__main__":
    test_pd_read_sql()
