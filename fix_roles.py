
import pandas as pd
from sqlalchemy import create_engine, text

db_url = 'sqlite:///ekleristan_local.db'
engine = create_engine(db_url)

print("=== CLEANING DUPLICATE ROLES ===")

with engine.connect() as conn:
    # 1. Identify duplicates
    df = pd.read_sql("SELECT * FROM ayarlar_roller", conn)
    
    # Reset index for safety
    df = df.reset_index(drop=True)
    
    # Find duplicate role names
    dups = df[df.duplicated(subset=['rol_adi'], keep='first')]
    
    if dups.empty:
        print("No duplicates found.")
    else:
        print(f"Found {len(dups)} duplicates to remove:")
        print(dups[['id', 'rol_adi']])
        
        # Delete duplicates by ID
        ids_to_del = dups['id'].tolist()
        if ids_to_del:
            ids_str = ','.join(map(str, ids_to_del))
            sql = text(f"DELETE FROM ayarlar_roller WHERE id IN ({ids_str})")
            conn.execute(sql)
            conn.commit()
            print(f"Successfully deleted IDs: {ids_str}")

    # Verify
    df_after = pd.read_sql("SELECT * FROM ayarlar_roller", conn)
    print("\nRemaining Roles:")
    print(df_after[['id', 'rol_adi']].to_string())
