from sqlalchemy import create_engine, text
import pandas as pd

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("--- AKILLI ROL DÜZELTME (SMART FIX) ---")
        
        # 1. Fetch all users with missing roles
        sql_missing = text("SELECT id, ad_soyad, gorev FROM personel WHERE rol IS NULL OR rol = ''")
        users = conn.execute(sql_missing).fetchall()
        
        print(f"Toplam {len(users)} rolü eksik personel bulundu.")
        
        updates = []
        for u in users:
            uid = u.id
            name = u.ad_soyad
            gorev = str(u.gorev).upper() if u.gorev else ""
            
            new_role = "Personel" # Default
            
            # MAPPING LOGIC
            if "SORUMLU" in gorev or "AMİR" in gorev or "KOORDİNATÖR" in gorev or "YÖNETİCİ" in gorev:
                new_role = "BÖLÜM SORUMLUSU" # DB'deki tam karşılığı: 'BÖLÜM SORUMLUSU' (ID 7)
                # Not: DB'de rol string olarak tutuluyorsa (ki öyle görünüyor), tam adı yazmalıyız.
                # Ancak constants.py veya app.py'de 'Bölüm Sorumlusu' olarak geçiyor olabilir.
                # Veritabanındaki diğer kayıtlara bakalım:
            elif "MÜHENDİS" in gorev:
                new_role = "Gıda Mühendisi"
            elif "GENEL MÜDÜR" in gorev:
                new_role = "Admin" # veya Genel Müdür
            
            # Case Adjustment based on existing DB values
            # Usually 'Personel', 'Bölüm Sorumlusu', 'Admin' (Title Case)
            if new_role == "BÖLÜM SORUMLUSU": new_role = "Bölüm Sorumlusu"
            
            updates.append({"id": uid, "rol": new_role})
            print(f" - {name} ({gorev}) -> {new_role}")

        # 2. Apply Updates
        if updates:
            print("\nUpdating database...")
            sql_update = text("UPDATE personel SET rol = :rol WHERE id = :id")
            conn.execute(sql_update, updates)
            conn.commit()
            print(f"✅ {len(updates)} kayıt güncellendi.")
        else:
            print("Güncellenecek kayıt bulunamadı.")
            
        # 3. Preventative: Cleanup Usernames (Trim whitespace)
        print("\n3. Genel Temizlik (Whitespace Trim)...")
        conn.execute(text("UPDATE personel SET kullanici_adi = TRIM(kullanici_adi), ad_soyad = TRIM(ad_soyad)"))
        conn.commit()

except Exception as e:
    print(f"Hata: {e}")
