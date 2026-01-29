import sqlite3
import pandas as pd

def upgrade_db():
    print(">>> Baslatiliyor: Yerel Veritabanı Yukseltme Islemi...")
    
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    # 1. 'ayarlar_bolumler' Tablosunu Güncelle (Eksik Kolonlar)
    try:
        print("--- Kontrol ediliyor: ayarlar_bolumler...")
        cursor.execute("PRAGMA table_info(ayarlar_bolumler)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'ana_departman_id' not in columns:
            print("  + 'ana_departman_id' kolonu ekleniyor...")
            cursor.execute("ALTER TABLE ayarlar_bolumler ADD COLUMN ana_departman_id INTEGER")
            
        if 'sira_no' not in columns:
            print("  + 'sira_no' kolonu ekleniyor...")
            cursor.execute("ALTER TABLE ayarlar_bolumler ADD COLUMN sira_no INTEGER DEFAULT 0")
            
        if 'aktif' not in columns:
            print("  + 'aktif' kolonu ekleniyor...")
            cursor.execute("ALTER TABLE ayarlar_bolumler ADD COLUMN aktif BOOLEAN DEFAULT 1")
            
        if 'aciklama' not in columns:
            print("  + 'aciklama' kolonu ekleniyor...")
            cursor.execute("ALTER TABLE ayarlar_bolumler ADD COLUMN aciklama TEXT")
            
    except Exception as e:
        print(f"❌ Hata (ayarlar_bolumler): {e}")

    # 2. Yeni Tabloları Oluştur (SQLite Syntax)
    
    # LOKASYONLAR
    print("--- Tablo olusturuluyor: lokasyonlar...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lokasyonlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ad TEXT NOT NULL,
        tip TEXT, -- 'Kat', 'Bölüm', 'Ekipman', 'Hat'
        parent_id INTEGER,
        sorumlu_id INTEGER,
        sira_no INTEGER DEFAULT 0,
        aktif BOOLEAN DEFAULT 1,
        sorumlu_departman TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(parent_id) REFERENCES lokasyonlar(id) ON DELETE SET NULL
    );
    """)

    # PROSES TİPLERİ
    print("--- Tablo olusturuluyor: proses_tipleri...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proses_tipleri (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kod TEXT UNIQUE NOT NULL,
        ad TEXT NOT NULL,
        ikon TEXT,
        modul_adi TEXT,
        aciklama TEXT,
        aktif BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    # Varsayılan veriler
    try:
        cursor.execute("INSERT OR IGNORE INTO proses_tipleri (kod, ad, ikon, modul_adi, aciklama) VALUES ('TEMIZLIK', 'Temizlik Kontrolü', '🧹', 'Temizlik Kontrol', 'Günlük/haftalık temizlik takibi')")
        cursor.execute("INSERT OR IGNORE INTO proses_tipleri (kod, ad, ikon, modul_adi, aciklama) VALUES ('KPI', 'KPI & Kalite Kontrol', '🍩', 'KPI Kontrol', 'Ürün kalite parametreleri ölçümü')")
        cursor.execute("INSERT OR IGNORE INTO proses_tipleri (kod, ad, ikon, modul_adi, aciklama) VALUES ('URETIM', 'Üretim Takibi', '🏭', 'Üretim Girişi', 'Üretim miktarları ve lot takibi')")
        cursor.execute("INSERT OR IGNORE INTO proses_tipleri (kod, ad, ikon, modul_adi, aciklama) VALUES ('GMP', 'GMP Denetimi', '🛡️', 'GMP Denetimi', 'Good Manufacturing Practice kontrolleri')")
        cursor.execute("INSERT OR IGNORE INTO proses_tipleri (kod, ad, ikon, modul_adi, aciklama) VALUES ('HIJYEN', 'Personel Hijyen', '🧼', 'Personel Hijyen', 'Personel hijyen kontrolleri')")
    except Exception as e: print(f"  - Varsayılan veri hatası: {e}")

    # LOKASYON PROSES ATAMA
    print("--- Tablo olusturuluyor: lokasyon_proses_atama...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lokasyon_proses_atama (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lokasyon_id INTEGER,
        proses_tipi_id INTEGER,
        siklik TEXT,
        sorumlu_id INTEGER,
        notlar TEXT,
        aktif BOOLEAN DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(lokasyon_id, proses_tipi_id),
        FOREIGN KEY(lokasyon_id) REFERENCES lokasyonlar(id) ON DELETE CASCADE,
        FOREIGN KEY(proses_tipi_id) REFERENCES proses_tipleri(id) ON DELETE CASCADE
    );
    """)

    # KİMYASAL ENVANTER (Kontrol)
    print("--- Kontrol ediliyor: kimyasal_envanter...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kimyasal_envanter (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kimyasal_adi TEXT NOT NULL,
        tedarikci TEXT,
        msds_yolu TEXT,
        tds_yolu TEXT,
        aktif BOOLEAN DEFAULT 1
    );
    """)

    # TANIM METOTLAR (Kontrol)
    print("--- Kontrol ediliyor: tanim_metotlar...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tanim_metotlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metot_adi TEXT NOT NULL,
        aciklama TEXT,
        aktif BOOLEAN DEFAULT 1
    );
    """)

    # GMP SORU HAVUZU (Kontrol + Eksik Kolon)
    print("--- Kontrol ediliyor: gmp_soru_havuzu...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gmp_soru_havuzu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kategori TEXT,
        soru_metni TEXT,
        risk_puani INTEGER,
        brc_ref TEXT,
        frekans TEXT,
        lokasyon_ids TEXT,
        aktif BOOLEAN DEFAULT 1
    );
    """)
    # lokasyon_ids kolonu kontrol
    try:
        cursor.execute("PRAGMA table_info(gmp_soru_havuzu)")
        gmp_cols = [c[1] for c in cursor.fetchall()]
        if 'lokasyon_ids' not in gmp_cols:
            print("  + 'lokasyon_ids' kolonu ekleniyor...")
            cursor.execute("ALTER TABLE gmp_soru_havuzu ADD COLUMN lokasyon_ids TEXT")
    except: pass

    conn.commit()
    conn.close()
    print("\n[OK] Yukseltme Islemi Basariyla Tamamlandi!")
    print("Artık Lokal Veritabanı, Canlı (Supabase) Şeması ile uyumlu.")

if __name__ == "__main__":
    upgrade_db()
