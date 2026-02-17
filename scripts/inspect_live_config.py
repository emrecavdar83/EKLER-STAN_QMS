import sqlalchemy
from sqlalchemy import text
import toml
import pandas as pd

def check_live_config():
    # Load secrets
    secrets = toml.load(".streamlit/secrets.toml")
    db_url = (secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")).strip('"')
    
    engine = sqlalchemy.create_engine(db_url)
    
    with engine.connect() as conn:
        print("--- AYARLAR_BOLUMLER ---")
        bolumler = pd.read_sql("SELECT * FROM ayarlar_bolumler", conn)
        print(bolumler)
        
        print("\n--- AYARLAR_ROLLER ---")
        try:
            roller = pd.read_sql("SELECT * FROM ayarlar_roller", conn)
            print(roller)
        except Exception as e:
            print(f"Error reading ayarlar_roller: {e}")

if __name__ == "__main__":
    check_live_config()
