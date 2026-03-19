
import sqlalchemy
from sqlalchemy import text, create_engine
import toml

def guarantee():
    secrets = toml.load(".streamlit/secrets.toml")
    db_url = secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")
    engine = create_engine(db_url)
    
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE soguk_odalar ADD COLUMN last_rule_hash TEXT"))
            print("Successfully added last_rule_hash column.")
        except Exception as e:
            print(f"Column may already exist: {e}")

if __name__ == "__main__":
    guarantee()
