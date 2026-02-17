
import pandas as pd
from sqlalchemy import create_engine, text

db_url = 'sqlite:///ekleristan_local.db'
engine = create_engine(db_url)

print("=== FIXING PERSONEL DEPARTMENT NAMES ===")

with engine.connect() as conn:
    # 1. Get correct mapping from IDs
    sql_mapping = "SELECT id, bolum_adi FROM ayarlar_bolumler"
    df_dept = pd.read_sql(sql_mapping, conn)
    dept_map = df_dept.set_index('id')['bolum_adi'].to_dict()
    
    # 2. Get users with departman_id
    users = pd.read_sql("SELECT id, ad_soyad, bolum, departman_id FROM personel WHERE departman_id IS NOT NULL", conn)
    
    updated_count = 0
    
    for _, row in users.iterrows():
        p_id = row['id']
        curr_bolum = row['bolum']
        dept_id = row['departman_id']
        
        if dept_id in dept_map:
            target_bolum = dept_map[dept_id]
            
            # Update only if different
            if curr_bolum != target_bolum:
                # Remove arrows/dots logic check if it is just a formatting issue
                # Actually, simply enforcing the clean name is best
                print(f"Fixing User {row['ad_soyad']} (ID {p_id}): '{curr_bolum}' -> '{target_bolum}'")
                
                update_sql = text("UPDATE personel SET bolum = :b WHERE id = :id")
                conn.execute(update_sql, {"b": target_bolum, "id": p_id})
                updated_count += 1
                
    conn.commit()
    print(f"\nTotal users updated: {updated_count}")
