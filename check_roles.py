
import pandas as pd
from sqlalchemy import create_engine, text

db_url = 'sqlite:///ekleristan_local.db'
engine = create_engine(db_url)

print("=== AYARLAR ROLLER (Checking Duplicates) ===")
with engine.connect() as conn:
    df = pd.read_sql("SELECT * FROM ayarlar_roller", conn)
    print(df.to_string())
    
    # Check for duplicates by name
    dups = df[df.duplicated(subset=['rol_adi'], keep=False)]
    if not dups.empty:
        print("\n!!! DUPLICATES FOUND !!!")
        print(dups.to_string())
