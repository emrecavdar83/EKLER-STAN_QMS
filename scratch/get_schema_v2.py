import sys
import os
from sqlalchemy import text

# Add workspace to path
sys.path.append(os.getcwd())

from database.connection import get_engine

def get_personel_schema():
    print("--- FETCHING PERSONEL SCHEMA ---")
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Get columns from information_schema
            query = text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'personel'
                ORDER BY ordinal_position;
            """)
            res = conn.execute(query).fetchall()
            
            if not res:
                print("Table 'personel' not found!")
                return
                
            print(f"{'COLUMN':<25} | {'TYPE':<15} | {'NULL':<10} | {'DEFAULT'}")
            print("-" * 70)
            for r in res:
                print(f"{str(r[0]):<25} | {str(r[1]):<15} | {str(r[2]):<10} | {str(r[3])}")
                
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    get_personel_schema()
