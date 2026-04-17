import sys
import os
from sqlalchemy import text

# Add workspace to path
sys.path.append(os.getcwd())

from database.connection import get_engine

def get_personel_cols():
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Query the columns directly
            res = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'personel'")).fetchall()
            if not res:
                print("TABLE NOT FOUND: personel")
                return
                
            print(f"--- COLUMNS FOR 'personel' ---")
            for r in res:
                print(f"{r[0]}: {r[1]}")
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    get_personel_cols()
