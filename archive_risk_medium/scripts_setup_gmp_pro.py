import sqlite3

def setup_gmp_tables():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    # 1. GMP Lokasyonlar
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gmp_lokasyonlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        lokasyon_adi TEXT NOT NULL,
        parent_id INTEGER,
        FOREIGN KEY (parent_id) REFERENCES gmp_lokasyonlar(id)
    )
    ''')
    
    # 2. GMP Soru Havuzu (BRC V9 Uyumlu)
    # Mevcut tabloyu kontrol et veya yeni yapıya güncelle
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gmp_soru_havuzu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kategori TEXT NOT NULL,
        soru_metni TEXT NOT NULL,
        risk_puani INTEGER DEFAULT 1,
        brc_ref TEXT,
        frekans TEXT DEFAULT 'GÜNLÜK',
        aktif BOOLEAN DEFAULT 1
    )
    ''')
    
    # 3. GMP Denetim Kayitlari
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gmp_denetim_kayitlari (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tarih DATE NOT NULL,
        saat TEXT,
        kullanici TEXT NOT NULL,
        lokasyon_id INTEGER,
        soru_id INTEGER,
        durum TEXT NOT NULL, -- 'UYGUN' veya 'UYGUN DEĞİL'
        fotograf_yolu TEXT,
        notlar TEXT,
        brc_ref TEXT,
        risk_puani INTEGER,
        FOREIGN KEY (lokasyon_id) REFERENCES gmp_lokasyonlar(id),
        FOREIGN KEY (soru_id) REFERENCES gmp_soru_havuzu(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("GMP Tabloları başarıyla oluşturuldu.")

if __name__ == "__main__":
    setup_gmp_tables()
