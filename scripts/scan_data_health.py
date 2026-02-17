from sqlalchemy import create_engine, text
import pandas as pd

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("--- GÜVENLİK TARAMASI: EKSİK VERİLİ PERSONELLER ---")
        
        # 1. Rolü Boş Olanlar
        print("\n1. ROLÜ TANIMLANMAMIŞ PERSONELLER (Görünürlük Sorunu Yaşayanlar):")
        sql_no_role = text("SELECT id, ad_soyad, kullanici_adi, departman_id, vardiya FROM personel WHERE rol IS NULL OR rol = ''")
        no_role = conn.execute(sql_no_role).fetchall()
        
        if no_role:
            print(f"⚠️ TOPLAM {len(no_role)} KİŞİDE ROL HATASI VAR!")
            for u in no_role:
                print(f" - ID: {u.id} | İsim: {u.ad_soyad} | BölümID: {u.departman_id}")
        else:
            print("✅ Rol verileri temiz.")

        # 2. Departmanı Boş Olanlar
        print("\n2. DEPARTMANI BAĞLANMAMIŞ PERSONELLER:")
        sql_no_dept = text("SELECT id, ad_soyad FROM personel WHERE departman_id IS NULL OR departman_id = 0")
        no_dept = conn.execute(sql_no_dept).fetchall()
        if no_dept:
             print(f"⚠️ TOPLAM {len(no_dept)} KİŞİNİN DEPARTMANI YOK!")
             # İlk 5'i göster
             for u in no_dept[:5]: print(f" - {u.ad_soyad}")
             if len(no_dept) > 5: print("...")

except Exception as e:
    print(f"Hata: {e}")
