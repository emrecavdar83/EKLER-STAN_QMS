from sqlalchemy import create_engine, text
import pandas as pd

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("--- SEARCHING 'YELİZ' ---")
        
        # 1. Search for user
        sql_user = text("SELECT * FROM personel WHERE ad_soyad LIKE '%YELİZ%' OR ad_soyad LIKE '%YELIZ%' OR kullanici_adi LIKE '%yeliz%'")
        users = conn.execute(sql_user).fetchall()
        
        if not users:
            print("❌ User not found!")
        else:
            for u in users:
                print(f"\nUser Found: {u.ad_soyad} (ID: {u.id})")
                print(f" - Username: {u.kullanici_adi}")
                print(f" - Role: {u.rol}")
                print(f" - Dept ID: {u.departman_id}")
                print(f" - Shift: {u.vardiya}")
                print(f" - Status: {u.durum}")
                
                # Check Department Name
                if u.departman_id:
                    sql_dept = text("SELECT * FROM ayarlar_bolumler WHERE id = :did")
                    dept = conn.execute(sql_dept, {"did": u.departman_id}).fetchone()
                    if dept:
                        print(f" - Dept Name (from DB): {dept.bolum_adi}")
                    else:
                        print(" - Dept Name: ❌ Invalid Department ID")
                else:
                    print(" - Dept Name: None")

                # Check Permissions/Visibility logic (Simulation)
                print("\n--- VISIBILITY SIMULATION ---")
                # Assume she wants to see her own department
                if u.departman_id:
                    print(f"Searching for other active personel in Dept ID {u.departman_id}...")
                    sql_team = text("""
                        SELECT ad_soyad, vardiya, durum 
                        FROM personel 
                        WHERE departman_id = :did AND durum = 'AKTİF'
                    """)
                    team = conn.execute(sql_team, {"did": u.departman_id}).fetchall()
                    print(f"Found {len(team)} team members:")
                    for t in team:
                        print(f" - {t.ad_soyad} ({t.vardiya})")
                
except Exception as e:
    print(e)
