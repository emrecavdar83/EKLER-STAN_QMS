# v5.8.14: EKLERİSTAN QMS - Robust Database Module Cleaner
import os
import sys

# Proje kök dizinini path'e ekle
sys.path.append(os.getcwd())

try:
    from database.connection import get_engine
    from sqlalchemy import text
    import pandas as pd
    
    engine = get_engine()
    print("🚀 Veritabanı temizlik işlemi (Robust v2) başlatılıyor...")
    
    with engine.begin() as conn:
        # 0. Tablo kolonlarını kontrol et (Schema Agnostic)
        # PostgreSQL için information_schema kullan
        col_query = text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ayarlar_moduller'
        """)
        columns = [r[0] for r in conn.execute(col_query).fetchall()]
        print(f"📋 Tespit edilen sütunlar: {columns}")
        
        has_durum = 'durum' in columns
        has_sira_no = 'sira_no' in columns

        # 1. 'Performans', 'Polivalans' veya 'Yetkinlik' içeren tüm satırları temizle
        sql_delete = text("""
            DELETE FROM ayarlar_moduller 
            WHERE LOWER(modul_anahtari) LIKE '%performans%' 
               OR LOWER(modul_anahtari) LIKE '%polivalans%' 
               OR LOWER(modul_anahtari) LIKE '%yetkinlik%'
               OR modul_etiketi LIKE '%Performans%'
               OR modul_etiketi LIKE '%Yetkinlik%'
        """)
        conn.execute(sql_delete)
        print("🗑️ Mükerrer performans/yetkinlik kayıtları silindi.")
        
        # 2. Tekil ve Standart Kaydı Ekle
        fields = ["modul_etiketi", "modul_anahtari"]
        values = {"label": "📈 Yetkinlik & Performans", "slug": "performans_polivalans"}
        
        if has_durum:
            fields.append("durum")
            values["durum"] = "AKTİF"
        if has_sira_no:
            fields.append("sira_no")
            values["sira_no"] = 100
            
        sql_insert = text(f"""
            INSERT INTO ayarlar_moduller ({', '.join(fields)})
            VALUES ({', '.join([':'+k for k in values.keys()])})
        """)
        
        # Sütun adları ile değer anahtarlarını eşleştir (label -> modul_etiketi, slug -> modul_anahtari)
        mapped_values = {}
        if "modul_etiketi" in fields: mapped_values["label"] = values["label"]
        if "modul_anahtari" in fields: mapped_values["slug"] = values["slug"]
        if "durum" in fields: mapped_values["durum"] = values["durum"]
        if "sira_no" in fields: mapped_values["sira_no"] = values["sira_no"]

        conn.execute(sql_insert, mapped_values)
        print(f"✨ Standardize edilmiş modül eklendi: 📈 Yetkinlik & Performans")
        
    print("\n✅ Temizlik başarıyla tamamlandı! Lütfen uygulamayı yenileyin.")

except Exception as e:
    print(f"❌ HATA: {e}")
