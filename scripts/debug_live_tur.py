
import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

def check_tur_values():
    print("--- LIVE DB DIAGNOSTIC ---")
    if os.path.exists(".streamlit/secrets.toml"):
        secrets = toml.load(".streamlit/secrets.toml")
        url = secrets["streamlit"]["DB_URL"]
        if url.startswith('"') and url.endswith('"'): url = url[1:-1]
        
        try:
            engine = create_engine(url)
            with engine.connect() as conn:
                # Get distribution
                print("Checking 'ayarlar_urunler' columns...")
                df = pd.read_sql("SELECT * FROM ayarlar_urunler LIMIT 1", conn)
                print(df.columns.tolist())
                
                print("\nFetching sample columns...")
                df_sample = pd.read_sql("SELECT id, bolum_adi, tur FROM ayarlar_bolumler LIMIT 10", conn)
                print(df_sample)
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_tur_values()
