import os
import toml
from sqlalchemy import create_engine, text

def run_migration():
    secrets_path = ".streamlit/secrets.toml"
    if not os.path.exists(secrets_path):
        print("Secrets file not found.")
        return

    secrets = toml.load(secrets_path)
    db_url = secrets.get("streamlit", {}).get("DB_URL")
    if not db_url:
        print("DB_URL not found in secrets.")
        return

    print(f"Connecting to: {db_url.split('@')[1]}") # Censored connection log
    engine = create_engine(db_url)
    
    sql_file = "migrations/20260318_qdms_schema.sql"
    if not os.path.exists(sql_file):
        print(f"{sql_file} not found.")
        return

    with open(sql_file, "r", encoding="utf-8") as f:
        # Split by ';' but avoid splitting within triggers/functions if they existed
        # This script doesn't have them, so simple split is fine.
        sql_script = f.read()
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]

    try:
        with engine.begin() as conn:
            for i, stmt in enumerate(statements):
                try:
                    print(f"Executing statement {i+1}/{len(statements)}...")
                    conn.execute(text(stmt))
                except Exception as inner_e:
                    print(f"Statement {i+1} FAILED: {inner_e}")
                    # We might want to continue or stop. Usually stop in engine.begin() rolls back.
                    raise
        print("Migration completed successfully.")
    except Exception as e:
        print(f"Overall Migration FAILED: {e}")

if __name__ == "__main__":
    run_migration()
