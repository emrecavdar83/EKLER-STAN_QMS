from sqlalchemy import create_engine, text
import pandas as pd

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("--- TARGETED SEARCH: YELİZ ---")
        
        # 1. Search by various variations
        sql_user = text("""
            SELECT p.id, p.ad_soyad, p.kullanici_adi, p.rol, p.vardiya, p.durum, p.departman_id, d.bolum_adi
            FROM personel p
            LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
            WHERE p.ad_soyad LIKE '%YELİZ%' OR p.kullanici_adi LIKE '%yeliz%'
        """)
        users = conn.execute(sql_user).fetchall()
        
        if not users:
            print("❌ 'YELİZ' not found in any form!")
        else:
            for u in users:
                print(f"ID: {u.id}")
                print(f"Name: {u.ad_soyad}")
                print(f"Username: {u.kullanici_adi}")
                print(f"Role: {u.rol}")
                print(f"Dept ID: {u.departman_id}")
                print(f"Dept Name (DB): {u.bolum_adi}")
                print(f"Shift: {u.vardiya}")
                print(f"Status: {u.durum}")
                
                # Check mismatch
                if not u.departman_id:
                     print("⚠️ WARNING: No Department ID!")
                
                if not u.bolum_adi:
                     print("⚠️ WARNING: No Department Name (Join Failed or NULL)!")

                # Check if anyone else is in this department/shift
                if u.departman_id:
                    sql_counts = text("""
                        SELECT COUNT(*) 
                        FROM personel 
                        WHERE departman_id = :did AND durum = 'AKTİF'
                    """)
                    count = conn.execute(sql_counts, {"did": u.departman_id}).scalar()
                    print(f"Total Active People in Dept {u.departman_id}: {count}")
                    
                    if u.vardiya:
                         sql_shift_counts = text("""
                            SELECT COUNT(*) 
                            FROM personel 
                            WHERE departman_id = :did AND durum = 'AKTİF' AND vardiya = :v
                        """)
                         count_shift = conn.execute(sql_shift_counts, {"did": u.departman_id, "v": u.vardiya}).scalar()
                         print(f"Total Active People in Dept {u.departman_id} & Shift '{u.vardiya}': {count_shift}")

                print("-" * 30)

except Exception as e:
    print(f"Error: {e}")
