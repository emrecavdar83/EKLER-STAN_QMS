
import pandas as pd
from sqlalchemy import create_engine, text

local_engine = create_engine('sqlite:///ekleristan_local.db')

print("=== DEEP LOCAL ROLE CHECK ===")
with local_engine.connect() as conn:
    df = pd.read_sql("SELECT * FROM ayarlar_roller", conn)
    print(f"Total rows: {len(df)}")
    
    # Check normalized duplicates
    df['norm'] = df['rol_adi'].str.strip().str.upper()
    dups = df[df.duplicated(subset=['norm'], keep=False)]
    if not dups.empty:
        print("\nDUPLICATES DETECTED (Normalized):")
        print(dups.to_string())
    else:
        print("\nNo normalized duplicates found.")
