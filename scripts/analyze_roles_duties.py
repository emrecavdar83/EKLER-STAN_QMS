from sqlalchemy import create_engine, text
import pandas as pd

try:
    engine = create_engine('sqlite:///ekleristan_local.db')
    with engine.connect() as conn:
        print("--- SİSTEMDEKİ GERÇEK TANIMLAMALAR (DATA DUMP) ---")
        
        # 1. Valid Roles (Sistemde şu an var olan Roller)
        print("\n1. MEVCUT KULLANILAN ROLLER (Valid Roles):")
        roles = conn.execute(text("SELECT DISTINCT rol FROM personel WHERE rol IS NOT NULL AND rol != ''")).fetchall()
        valid_roles = [r[0] for r in roles]
        for r in valid_roles:
            print(f"  - {r}")

        # 2. Yetki Tablosundaki Roller (Authoritative List)
        print("\n2. YETKİ TABLOSUNDAKİ ROLLER (Ayarlar_Yetkiler):")
        try:
            auth_roles = conn.execute(text("SELECT DISTINCT rol_adi FROM ayarlar_yetkiler")).fetchall()
            for r in auth_roles:
                print(f"  - {r[0]}")
        except:
            print("  (Ayarlar_Yetkiler tablosu okunamadı)")

        # 3. Missing Roles & Their Duties (Sorunlu Kayıtlar ne iş yapıyor?)
        print("\n3. ROLÜ OLMAYANLARIN GÖREV DAĞILIMI (Örnekleme):")
        sql_missing = text("""
            SELECT gorev, COUNT(*) as kisi_sayisi 
            FROM personel 
            WHERE (rol IS NULL OR rol = '') 
            GROUP BY gorev 
            ORDER BY kisi_sayisi DESC
        """)
        missing_stats = conn.execute(sql_missing).fetchall()
        
        for row in missing_stats:
            gorev = row[0] if row[0] else "(Boş/Yok)"
            count = row[1]
            print(f"  - Görev: '{gorev}' -> {count} Kişi (Örn: Yeliz Çakır bu grupta olabilir)")

        # 4. Yeliz Review
        print("\n4. ÖRNEK VAKA: YELİZ ÇAKIR")
        yeliz = conn.execute(text("SELECT ad_soyad, gorev, rol FROM personel WHERE ad_soyad LIKE '%YELİZ ÇAKIR%'")).fetchone()
        if yeliz:
            print(f"  - Ad: {yeliz[0]}")
            print(f"  - Şu Anki Görev Verisi: '{yeliz[1]}'")
            print(f"  - Şu Anki Rol: '{yeliz[2]}'")
            
except Exception as e:
    print(f"Hata: {e}")
