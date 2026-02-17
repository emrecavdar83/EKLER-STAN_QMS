
import pandas as pd
from sqlalchemy import create_engine

local_engine = create_engine('sqlite:///ekleristan_local.db')

print("=== LOCAL PERMISSIONS DEEP CHECK ===")
with local_engine.connect() as conn:
    df = pd.read_sql("SELECT * FROM ayarlar_yetkiler", conn)
    
    df['rol_norm'] = df['rol_adi'].str.strip().str.upper()
    df['mod_norm'] = df['modul_adi'].str.strip().str.upper()
    
    dup_keys = df[df.duplicated(subset=['rol_norm', 'mod_norm'], keep=False)]
    if not dup_keys.empty:
        print("\nDUPLICATE (Normalized Status):")
        print(dup_keys.sort_values(['rol_norm', 'mod_norm']).to_string())
    else:
        print("No normalized duplicates.")
