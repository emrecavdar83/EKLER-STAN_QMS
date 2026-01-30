
from sqlalchemy import create_engine, text
import pandas as pd

engine = create_engine('sqlite:///ekleristan_local.db')

try:
    with engine.connect() as conn:
        # Check table info
        info = pd.read_sql("PRAGMA table_info(personel)", conn)
        print("COLUMNS:")
        print(info[['name', 'type']])
        
        # Check current data sample
        sample = pd.read_sql("SELECT id, ad_soyad, departman_id, bolum FROM personel LIMIT 5", conn)
        print("\nSAMPLE DATA:")
        print(sample)
except Exception as e:
    print(e)
