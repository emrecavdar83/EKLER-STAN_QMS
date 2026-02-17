
import pandas as pd
from sqlalchemy import create_engine, text

local_engine = create_engine('sqlite:///ekleristan_local.db')

print("=== FIXING LOCAL PERMISSION ROLE NAMES ===")

with local_engine.connect() as conn:
    # 1. Get official roles
    df_roles = pd.read_sql("SELECT rol_adi FROM ayarlar_roller", conn)
    official_roles = set(df_roles['rol_adi'].tolist())
    
    # 2. Get current permissions
    df_perms = pd.read_sql("SELECT * FROM ayarlar_yetkiler", conn)
    
    # 3. Find mismatches
    current_roles = set(df_perms['rol_adi'].tolist())
    mismatches = current_roles - official_roles
    
    if mismatches:
        print(f"Found mismatched roles in permissions: {mismatches}")
        
        # Fixing logic (Mapping based on content)
        # 'KALITE SORUMLUSU' -> 'KALİTE SORUMLSU'
        # 'KALİTE SORUMLUSU' -> 'KALİTE SORUMLSU'
        
        mapping = {
            'KALITE SORUMLUSU': 'KALİTE SORUMLSU',
            'KALİTE SORUMLUSU': 'KALİTE SORUMLSU'
        }
        
        for old, new in mapping.items():
            if old in mismatches:
                print(f"Mapping '{old}' -> '{new}'")
                conn.execute(text("UPDATE ayarlar_yetkiler SET rol_adi = :new WHERE rol_adi = :old"), {"new": new, "old": old})
        
        conn.commit()
        print("Update complete.")
    else:
        print("No mismatches found.")
