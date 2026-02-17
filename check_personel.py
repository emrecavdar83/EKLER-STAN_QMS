
import pandas as pd
from sqlalchemy import create_engine, text

db_url = 'sqlite:///ekleristan_local.db'
engine = create_engine(db_url)

with engine.connect() as conn:
    df = pd.read_sql("SELECT * FROM personel LIMIT 1", conn)
    print("Personel Columns:", df.columns.tolist())
    
    # Check if 'bolum' exists in columns
    if 'bolum' in df.columns.tolist():
        print("WARNING: 'bolum' column exists in 'personel' table!")
