import sqlite3
import os

def align_db():
    db_path = 'ekleristan_local.db'
    if not os.path.exists(db_path):
        print(f"HATA: {db_path} bulunamadı!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"--- {db_path} Şema Hizalama Başlatıldı ---")

    # 1. PERSONEL Tablosu Güncelleme
    print("Personel tablosu kontrol ediliyor...")
    cursor.execute("PRAGMA table_info(personel)")
    cols = [col[1] for col in cursor.fetchall()]
    
    if 'departman_id' not in cols:
        print("-> departman_id ekleniyor...")
        cursor.execute("ALTER TABLE personel ADD COLUMN departman_id INTEGER")
    if 'yonetici_id' not in cols:
        print("-> yonetici_id ekleniyor...")
        cursor.execute("ALTER TABLE personel ADD COLUMN yonetici_id INTEGER")
    if 'pozisyon_seviye' not in cols:
        print("-> pozisyon_seviye ekleniyor...")
        cursor.execute("ALTER TABLE personel ADD COLUMN pozisyon_seviye INTEGER DEFAULT 5")
    if 'ise_giris_tarihi' not in cols:
        print("-> ise_giris_tarihi ekleniyor...")
        cursor.execute("ALTER TABLE personel ADD COLUMN ise_giris_tarihi TEXT")
    if 'izin_gunu' not in cols:
        print("-> izin_gunu ekleniyor...")
        cursor.execute("ALTER TABLE personel ADD COLUMN izin_gunu TEXT")

    # 2. AYARLAR_TEMIZLIK_PLANI Tablosu (Kat sütunu ve diğerleri)
    print("Temizlik planı tablosu kontrol ediliyor...")
    cursor.execute("PRAGMA table_info(ayarlar_temizlik_plani)")
    cols = [col[1] for col in cursor.fetchall()]
    
    if 'kat' not in cols:
        print("-> kat ekleniyor...")
        cursor.execute("ALTER TABLE ayarlar_temizlik_plani ADD COLUMN kat TEXT")
    if 'validasyon_siklik' not in cols:
        cursor.execute("ALTER TABLE ayarlar_temizlik_plani ADD COLUMN validasyon_siklik TEXT")
    if 'verifikasyon' not in cols:
        cursor.execute("ALTER TABLE ayarlar_temizlik_plani ADD COLUMN verifikasyon TEXT")
    if 'verifikasyon_siklik' not in cols:
        cursor.execute("ALTER TABLE ayarlar_temizlik_plani ADD COLUMN verifikasyon_siklik TEXT")

    # 3. YENİ TABLOLAR (Eksikse oluştur)
    print("Eksik tablolar oluşturuluyor...")
    
    # GMP Soru Havuzu (Yeni kolonlar dahil)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gmp_soru_havuzu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kategori TEXT NOT NULL,
        soru_metni TEXT NOT NULL,
        risk_puani INTEGER DEFAULT 1,
        brc_ref TEXT,
        frekans TEXT DEFAULT 'GÜNLÜK',
        aktif BOOLEAN DEFAULT 1,
        lokasyon_ids TEXT
    )""")

    # GMP Denetim Kayıtları
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gmp_denetim_kayitlari (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarih TEXT NOT NULL,
        saat TEXT,
        kullanici TEXT NOT NULL,
        lokasyon_id INTEGER,
        soru_id INTEGER,
        durum TEXT NOT NULL,
        fotograf_yolu TEXT,
        notlar TEXT,
        brc_ref TEXT,
        risk_puani INTEGER
    )""")

    # Lokasyonlar (Hiyerarşik Yapı)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lokasyonlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad TEXT NOT NULL,
        tip TEXT,
        parent_id INTEGER,
        sorumlu_id INTEGER,
        sira_no INTEGER DEFAULT 0,
        aktif BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()
    conn.close()
    print("--- Şema Hizalama Başarıyla Tamamlandı ---")

if __name__ == "__main__":
    align_db()
