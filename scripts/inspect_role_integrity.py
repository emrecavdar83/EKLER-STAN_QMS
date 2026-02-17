from sqlalchemy import create_engine, text
import pandas as pd

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("--- AKILLI ROL ANALİZİ (SMART DATA INSPECTION) ---")
        
        # 1. Check all columns in 'personel' table to find 'gorev' or similar
        print("1. Table Columns:")
        # SQLite specific to get columns
        cols = conn.execute(text("PRAGMA table_info(personel)")).fetchall()
        col_names = [c[1] for c in cols]
        print(f"   Columns: {col_names}")
        
        has_gorev = 'gorev' in col_names
        
        # 2. Inspect users with missing roles
        print("\n2. Analyzing Users with Missing Roles:")
        
        query_cols = "id, ad_soyad, rol"
        if has_gorev: query_cols += ", gorev, pozisyon_seviye"
        else: query_cols += ", pozisyon_seviye"
            
        sql = text(f"SELECT {query_cols} FROM personel WHERE rol IS NULL OR rol = ''")
        users = conn.execute(sql).fetchall()
        
        if users:
            print(f"Found {len(users)} users. Sample data:")
            for u in users:
                gorev_val = u.gorev if has_gorev else "N/A"
                print(f" - ID: {u.id} | Name: {u.ad_soyad} | Gorev: {gorev_val} | Seviye: {u.pozisyon_seviye}")
                
            # 3. Analyze unique 'gorev' values to propose mappings
            if has_gorev:
                print("\n3. Unique 'Gorev' values found in missing list:")
                df = pd.DataFrame(users)
                if not df.empty and 'gorev' in df.columns:
                    print(df['gorev'].value_counts())
        else:
            print("No users with missing roles found (did previous fix run?).")

except Exception as e:
    print(f"Error: {e}")
