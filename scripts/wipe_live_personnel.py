
import toml
import os
from sqlalchemy import create_engine, text

def get_live_url():
    secrets_path = ".streamlit/secrets.toml"
    if not os.path.exists(secrets_path):
        return None
    
    secrets = toml.load(secrets_path)
    if "streamlit" in secrets and "DB_URL" in secrets["streamlit"]:
        url = secrets["streamlit"]["DB_URL"]
    elif "DB_URL" in secrets:
        url = secrets["DB_URL"]
    else:
        return None
        
    if url.startswith('"') and url.endswith('"'):
        url = url[1:-1]
    return url

def wipe_live_personnel():
    url = get_live_url()
    if not url:
        print("Error: Could not find live DB URL.")
        return

    print(f"Connecting to live DB: {url.split('@')[-1]}") # Print only host part for safety
    engine = create_engine(url)
    
    try:
        with engine.begin() as conn:
            print("Wiping live 'personel' table...")
            # For Postgres, TRUNCATE is faster and resets sequences
            conn.execute(text("TRUNCATE TABLE personel CASCADE"))
            print("Live 'personel' table wiped successfully.")
    except Exception as e:
        print(f"Error wiping live table: {e}")
    finally:
        engine.dispose()

if __name__ == "__main__":
    wipe_live_personnel()
