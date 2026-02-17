
import pandas as pd
from sqlalchemy import create_engine

local_engine = create_engine('sqlite:///ekleristan_local.db')

with local_engine.connect() as conn:
    df = pd.read_sql("SELECT * FROM ayarlar_yetkiler ORDER BY rol_adi, modul_adi", conn)
    # Check for normalized duplicates within this dataframe
    df['norm'] = df['rol_adi'].str.upper() + " | " + df['modul_adi'].str.upper()
    dups = df[df.duplicated(subset=['norm'], keep=False)]
    if not dups.empty:
        print("NORMALIZED DUPLICATES IN ayarlar_yetkiler:")
        print(dups.to_string())
    else:
        print("No normalized duplicates found.")
        
    print("\nFirst 20 rows:")
    print(df.head(20).to_string())
