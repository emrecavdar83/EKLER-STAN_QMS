
import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

def check_live():
    print("--- CHECKING LIVE DB ---")
    try:
        if os.path.exists(".streamlit/secrets.toml"):
            secrets = toml.load(".streamlit/secrets.toml")
            url = secrets["streamlit"]["DB_URL"]
            if url.startswith('"') and url.endswith('"'): url = url[1:-1]
            
            engine = create_engine(url)
            with engine.connect() as conn:
                try:
                    # 1. Check Column Existence
                    print("Checking schema...")
                    try:
                        res = conn.execute(text("SELECT tur FROM ayarlar_bolumler LIMIT 1"))
                        print("Column 'tur' EXISTS.")
                    except Exception as e:
                        print(f"Column 'tur' MISSING or Error: {e}")
                        return

                    # 2. Check Data Distribution
                    print("Checking data...")
                    df = pd.read_sql("SELECT id, bolum_adi, tur FROM ayarlar_bolumler", conn)
                    print(f"Total Rows: {len(df)}")
                    print("\nValue Counts for 'tur':")
                    print(df['tur'].value_counts(dropna=False))
                    print("\nFirst 10 Rows:")
                    print(df.head(10))
                    
                except Exception as e:
                    print(f"Query Error: {e}")
        else:
            print("Secrets not found.")
    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    check_live()
