import sqlite3
import os

# v5.5.3: Gerçek Veritabanı Yolu (connection.py'den teyit edildi)
DB_PATH = "ekleristan_local.db" 
LOCK_FILE = "tmp/v553_db_restore.lock"

def restore():
    print(f"🛡️ EKLERİSTAN QMS — v5.5.3 Fiziksel Restorasyon Başlatılıyor...")
    print(f"📂 Hedef Veritabanı: {DB_PATH}")
    
    if not os.path.exists("tmp"):
        os.makedirs("tmp")

    if not os.path.exists(DB_PATH):
        print(f"❌ KRİTİK HATA: {DB_PATH} dosyası bulunamadı! Lütfen dizini kontrol edin.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Tablo Varlık Kontrolü
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in cursor.fetchall()]
        print(f"📊 Mevcut Tablolar: {', '.join(tables[:5])}...")

        if 'personel' not in tables:
            print("❌ HATA: 'personel' tablosu bu veritabanında bulunamadı!")
            return

        # 1. Elvan Özdemirel Onarımı
        print("📍 Operasyon 1: Elvan Özdemirel kaydı temizleniyor...")
        cursor.execute("DELETE FROM personel WHERE kullanici_adi LIKE 'elvan.ozdemi%' AND kullanici_adi LIKE '%?%'")
        cursor.execute("UPDATE personel SET rol = 'BÖLÜM SORUMLUSU' WHERE kullanici_adi = 'elvan.ozdemirel'")
        
        # 2. Yetki Matrisi Normalizasyonu (Label -> Key)
        print("📍 Operasyon 2: Yetki matrisi normalizasyonu (Label -> Slug)...")
        norm_map = {
            "🏭 Üretim Girişi": "uretim_girisi", "🍩 KPI & Kalite Kontrol": "kpi_kontrol",
            "🛡️ GMP Denetimi": "gmp_denetimi", "🧼 Personel Hijyen": "personel_hijyen",
            "🧹 Temizlik Kontrol": "temizlik_kontrol", "📊 Kurumsal Raporlama": "kurumsal_raporlama",
            "❄️ Soğuk Oda Sıcaklıkları": "soguk_oda", "📦 MAP Üretim": "map_uretim",
            "📋 Günlük Görevler": "gunluk_gorevler", "📈 Yetkinlik & Performans": "performans_polivalans",
            "📁 QDMS": "qdms", "⚙️ Ayarlar": "ayarlar"
        }
        for label, key in norm_map.items():
            cursor.execute("UPDATE ayarlar_yetkiler SET modul_adi = ? WHERE modul_adi = ?", (key, label))

        # 3. Operatör MAP Yetkisi Garantisi
        print("📍 Operasyon 3: Operatör MAP yetkisi mühürleniyor...")
        cursor.execute("""
            INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu, sadece_kendi_bolumu)
            SELECT 'OPERATOR', 'map_uretim', 'Düzenle', 0
            WHERE NOT EXISTS (
                SELECT 1 FROM ayarlar_yetkiler WHERE rol_adi = 'OPERATOR' AND modul_adi = 'map_uretim'
            )
        """)
        
        conn.commit()
        
        with open(LOCK_FILE, "w") as f:
            f.write("v5.5.3 ABSOLUTE REALITY RESTORED")
        
        print("\n✅ MÜHÜRLENDİ: Veritabanı 'ekleristan_local.db' fiziksel olarak onarıldı.")
        print(f"📁 Kilit Dosyası: {LOCK_FILE}")

    except Exception as e:
        print(f"❌ HATA: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    restore()
