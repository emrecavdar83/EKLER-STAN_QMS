
import pandas as pd
from sqlalchemy import create_engine, text

local_engine = create_engine('sqlite:///ekleristan_local.db')

print("=== CLEANING LOCAL PERMISSIONS PROPERLY ===")

mapping = {
    'KALITE SORUMLUSU': 'KALİTE SORUMLSU',
    'KALİTE SORUMLUSU': 'KALİTE SORUMLSU',
    'KALITE SORUMLSU': 'KALİTE SORUMLSU'
}

with local_engine.connect() as conn:
    # 1. Fetch current data
    df = pd.read_sql("SELECT * FROM ayarlar_yetkiler", conn)
    print(f"Initial count: {len(df)}")
    
    # 2. Map role names
    df['rol_adi'] = df['rol_adi'].replace(mapping)
    
    # 3. Identify duplicates in the mapped data
    # We keep the first occurrence
    dups = df[df.duplicated(subset=['rol_adi', 'modul_adi'], keep='first')]
    
    if not dups.empty:
        print(f"Found {len(dups)} rows that will become duplicates. Deleting them...")
        ids_to_del = dups['id'].tolist()
        ids_str = ",".join(map(str, ids_to_del))
        conn.execute(text(f"DELETE FROM ayarlar_yetkiler WHERE id IN ({ids_str})"))
        conn.commit()
        print(f"Deleted IDs: {ids_str}")
    
    # 4. Now perform the role name updates for those remaining
    for old, new in mapping.items():
        conn.execute(text("UPDATE ayarlar_yetkiler SET rol_adi = :new WHERE rol_adi = :old"), {"new": new, "old": old})
    
    conn.commit()
    print("Local database cleaned.")

    # 5. Final check
    df_final = pd.read_sql("SELECT DISTINCT rol_adi FROM ayarlar_yetkiler", conn)
    print("\nFinal distinct roles in permissions:")
    for r in df_final['rol_adi']:
        print(f"'{r}'")
