import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from database.connection import get_engine
from sqlalchemy import text

def inspect_personel_schema():
    engine = get_engine()
    print("--- EXTRACTING PERSONEL SCHEMA ---")
    try:
        with engine.connect() as conn:
            # 1. Get column details
            sql_cols = text("""
                SELECT column_name, data_type, column_default, is_nullable, character_maximum_length
                FROM information_schema.columns 
                WHERE table_name = 'personel' 
                ORDER BY ordinal_position
            """)
            res = conn.execute(sql_cols).fetchall()
            
            columns = []
            for r in res:
                col_name, dtype, default, nullable, max_len = r
                col_def = f"{col_name} {dtype}"
                if max_len: col_def += f"({max_len})"
                if default: col_def += f" DEFAULT {default}"
                if nullable == 'NO': col_def += " NOT NULL"
                columns.append(col_def)
                print(f"Column: {col_def}")
            
            # 2. Get constraints
            sql_cons = text("""
                SELECT conname, pg_get_constraintdef(c.oid)
                FROM pg_constraint c
                JOIN pg_namespace n ON n.oid = c.connamespace
                WHERE contype IN ('p', 'u', 'f') AND conrelid = 'personel'::regclass
            """)
            res_cons = conn.execute(sql_cons).fetchall()
            print("\n--- CONSTRAINTS ---")
            for name, definition in res_cons:
                print(f"- {name}: {definition}")

            # 3. Get indexes
            sql_idx = text("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'personel'
            """)
            res_idx = conn.execute(sql_idx).fetchall()
            print("\n--- INDEXES ---")
            for name, definition in res_idx:
                print(f"- {name}: {definition}")
                
    except Exception as e:
        print(f"Error during inspection: {e}")

if __name__ == "__main__":
    inspect_personel_schema()
