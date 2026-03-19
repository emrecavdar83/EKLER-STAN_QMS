
import sqlalchemy
from sqlalchemy import text, create_engine
import toml

def add_column():
    secrets = toml.load(".streamlit/secrets.toml")
    db_url = secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")
    engine = create_engine(db_url)
    
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE olcum_plani ADD COLUMN bitis_zamani TIMESTAMP"))
            print("Successfully added bitis_zamani column.")
        except Exception as e:
            print(f"Error or already exists: {e}")

if __name__ == "__main__":
    add_column()
