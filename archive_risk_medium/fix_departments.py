import pandas as pd
from sqlalchemy import create_engine, text

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("Executing Department Fixes...")
        
        # 1. Fetch IDs
        df = pd.read_sql("SELECT id, bolum_adi FROM ayarlar_bolumler WHERE bolum_adi IN ('DOMBA', 'BOMBA', 'RULO PASTA', 'HALKA TATLI', 'ÜRETİM')", conn)
        id_map = {row['bolum_adi']: row['id'] for _, row in df.iterrows()}
        print(f"IDs Found: {id_map}")
        
        # 2. ÜRETİM LINKING
        uretim_id = id_map.get('ÜRETİM')
        if uretim_id:
            for dept in ['RULO PASTA', 'HALKA TATLI']:
                d_id = id_map.get(dept)
                if d_id:
                    print(f"Linking {dept} (ID: {d_id}) -> ÜRETİM (ID: {uretim_id})")
                    conn.execute(text("UPDATE ayarlar_bolumler SET ana_departman_id = :p WHERE id = :c"), {"p": uretim_id, "c": d_id})
        
        # 3. DOMBA -> BOMBA MERGE
        domba_id = id_map.get('DOMBA')
        bomba_id = id_map.get('BOMBA')
        
        if domba_id and bomba_id:
            print(f"Merging DOMBA ({domba_id}) into BOMBA ({bomba_id})...")
            # Move Personnel
            conn.execute(text("UPDATE personel SET departman_id = :new WHERE departman_id = :old"), {"new": bomba_id, "old": domba_id})
            # Delete DOMBA
            conn.execute(text("DELETE FROM ayarlar_bolumler WHERE id = :old"), {"old": domba_id})
            print("Merge Complete.")
            
        elif domba_id and not bomba_id:
            print(f"Renaming DOMBA ({domba_id}) -> BOMBA...")
            conn.execute(text("UPDATE ayarlar_bolumler SET bolum_adi = 'BOMBA' WHERE id = :id"), {"id": domba_id})
            
        conn.commit()
        print("✅ Department fixes applied successfully.")

except Exception as e:
    print(f"❌ Error: {e}")
