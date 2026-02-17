
import pandas as pd
from sqlalchemy import create_engine

local_engine = create_engine('sqlite:///ekleristan_local.db')

with local_engine.connect() as conn:
    df = pd.read_sql("SELECT rol_adi, modul_adi FROM ayarlar_yetkiler", conn)
    df = df.sort_values(['rol_adi', 'modul_adi'])
    
    # Check for duplicates explicitly here
    dups = df[df.duplicated(keep=False)]
    if not dups.empty:
        print("DUPLICATES FOUND:")
        print(dups.to_string())
    else:
        print("No duplicates found in raw data.")
        
    # Print all rows to be sure
    # print(df.to_string())
