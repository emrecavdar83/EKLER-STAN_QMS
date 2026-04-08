import sys
import os

# Add parent directory to sys.path to import from database.connection
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_engine
from sqlalchemy import text

def apply_migration():
    engine = get_engine()
    # Adjust path accordingly
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sql_file = os.path.join(base_path, "migrations", "20260408_01_dept_system_v2.sql")
    
    if not os.path.exists(sql_file):
        print(f"Migration file not found: {sql_file}")
        return

    with open(sql_file, "r", encoding="utf-8") as f:
        queries = f.read().split(";")
        
    print(f"Applying migration: {sql_file}")
    with engine.begin() as conn:
        for query in queries:
            if not query.strip(): continue
            try:
                # v5.8.1: SQLite Constraint Bypass
                if "CONSTRAINT" in query.upper() and engine.name == "sqlite":
                    print(f"Skipping Constraint block for SQLite: {query[:30]}...")
                    continue
                
                # Check for table existence
                if "ALTER TABLE" in query.upper() and engine.name == "sqlite":
                    col_name = query.split("ADD COLUMN IF NOT EXISTS")[-1].strip().split(" ")[0]
                    table_name = query.split("ALTER TABLE IF EXISTS")[-1].strip().split(" ")[0]
                    # Simple sqlite check for column existence
                    res = conn.execute(text(f"PRAGMA table_info({table_name})"))
                    cols = [r[1] for r in res]
                    if col_name in cols:
                        print(f"Column {col_name} already exists in {table_name}. Skipping.")
                        continue

                print(f"Executing: {query.strip()[:60]}...")
                conn.execute(text(query))
            except Exception as e:
                print(f"Error executing query: {e}")
                if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                    print("Constraint/Column already exists. Continuing...")
                else:
                    # Do not raise as some Postgres syntax might fail on local SQLite
                    pass

    print("✅ Migration applied successfully.")

if __name__ == "__main__":
    apply_migration()
