from sqlalchemy import create_engine, text
import pandas as pd

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("--- DETAILS FOR ID 182 (MİHRİMAH ALİ) ---")
        sql = text("SELECT * FROM personel WHERE id = 182")
        u = conn.execute(sql).fetchone()
        if u:
            print(f"Name: {u.ad_soyad}")
            print(f"Username: {u.kullanici_adi}")
            print(f"Password: {u.sifre}")
            print(f"DeptID: {u.departman_id}")
            print(f"Role: {u.rol}")
            print(f"Schift: {u.vardiya}")
            print(f"Status: {u.durum}")
            
            # Dept Name
            if u.departman_id:
                d = conn.execute(text("SELECT * FROM ayarlar_bolumler WHERE id = :did"), {"did": u.departman_id}).fetchone()
                print(f"Dept Name (from DB): {d.bolum_adi if d else 'NOT FOUND'}")
        
        print("\n--- CHECKING OTHER STAFF IN DEPT 22 (RULO PASTA) ---")
        sql2 = text("SELECT ad_soyad, vardiya, durum FROM personel WHERE departman_id = 22")
        others = conn.execute(sql2).fetchall()
        for o in others:
            print(f" - {o.ad_soyad} | Shift: {o.vardiya} | Status: {o.durum}")

except Exception as e:
    print(e)
