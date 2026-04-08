# v5.8.13: EKLERİSTAN QMS - Database Module Cleaner
import os
import sys

# Proje kök dizinini path'e ekle
sys.path.append(os.getcwd())

try:
    from database.connection import get_engine
    from sqlalchemy import text
    import pandas as pd
    
    engine = get_engine()
    print("🚀 Veritabanı temizlik işlemi başlatılıyor...")
    
    with engine.begin() as conn:
        # 1. Mevcut durumu kontrol et
        res = conn.execute(text("SELECT id, modul_etiketi, modul_anahtari FROM ayarlar_moduller")).fetchall()
        print(f"📊 Mevcut toplam modül sayısı: {len(res)}")
        
        # 2. 'Performans', 'Polivalans' veya 'Yetkinlik' içeren tüm satırları bul ve temizle
        target_slug = "performans_polivalans"
        target_label = "📈 Yetkinlik & Performans"
        
        # Fiziksel Silme (Performans varyasyonları için)
        sql_delete = text("""
            DELETE FROM ayarlar_moduller 
            WHERE LOWER(modul_anahtari) LIKE '%performans%' 
               OR LOWER(modul_anahtari) LIKE '%polivalans%' 
               OR LOWER(modul_anahtari) LIKE '%yetkinlik%'
               OR modul_etiketi LIKE '%Performans%'
        """)
        conn.execute(sql_delete)
        print("🗑️ Mükerrer performans kayıtları silindi.")
        
        # 3. Tekil ve Standart Kaydı Ekle
        sql_insert = text("""
            INSERT INTO ayarlar_moduller (modul_etiketi, modul_anahtari, durum, sira_no)
            VALUES (:label, :slug, 'AKTİF', 100)
        """)
        conn.execute(sql_insert, {"label": target_label, "slug": target_slug})
        print(f"✨ Standardize edilmiş modül eklendi: {target_label}")
        
    print("\n✅ Temizlik başarıyla tamamlandı! Lütfen uygulamayı yenileyin.")

except Exception as e:
    print(f"❌ HATA: {e}")
