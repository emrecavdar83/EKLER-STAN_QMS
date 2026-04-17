import sys
import os
from sqlalchemy import text

# Add workspace to path
sys.path.append(os.getcwd())

from database.connection import get_engine

def run_migration(sql_file):
    engine = get_engine()
    print(f"--- RUNNING MIGRATION: {sql_file} ---")
    
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
            
        # Split by BEGIN/COMMIT or just use the whole block if BEGIN exists
        # Actually, it's safer to execute individual statements or the whole block in a transaction
        
        with engine.begin() as conn:
            # We execute as a single block because of the BEGIN/COMMIT in the file
            conn.execute(text(sql_content))
            print("Migration executed successfully.")
            
    except Exception as e:
        print(f"ERROR executing migration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_migration(sys.argv[1])
    else:
        run_migration('migrations/20260417_user_table_unification.sql')
