import sqlite3

conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()

# Tabloları oluştur
cursor.execute('''
CREATE TABLE IF NOT EXISTS ayarlar_roller (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rol_adi TEXT UNIQUE NOT NULL,
    aciklama TEXT,
    aktif BOOLEAN DEFAULT 1,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS ayarlar_bolumler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bolum_adi TEXT UNIQUE NOT NULL,
    aciklama TEXT,
    aktif BOOLEAN DEFAULT 1,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS ayarlar_yetkiler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rol_adi TEXT NOT NULL,
    modul_adi TEXT NOT NULL,
    erisim_turu TEXT NOT NULL,
    UNIQUE(rol_adi, modul_adi)
)
''')

# Rolleri ekle
roller = [
    ('Admin', 'Sistem yoneticisi'),
    ('Kalite Sorumlusu', 'Kalite kontrol'),
    ('Vardiya Amiri', 'Vardiya yonetimi'),
    ('Personel', 'Temel kullanici'),
    ('Depo Sorumlusu', 'Depo yonetimi')
]

for rol in roller:
    cursor.execute('INSERT OR IGNORE INTO ayarlar_roller (rol_adi, aciklama) VALUES (?, ?)', rol)

# Bolumleri ekle
bolumler = [
    ('Uretim', 'Uretim hatti'),
    ('Paketleme', 'Paketleme'),
    ('Depo', 'Depo'),
    ('Ofis', 'Ofis'),
    ('Kalite', 'Kalite'),
    ('Yonetim', 'Yonetim'),
    ('Temizlik', 'Temizlik')
]

for bolum in bolumler:
    cursor.execute('INSERT OR IGNORE INTO ayarlar_bolumler (bolum_adi, aciklama) VALUES (?, ?)', bolum)

# Admin yetkileri
yetkiler = [
    ('Admin', 'Uretim Girisi', 'Duzenle'),
    ('Admin', 'KPI Kontrol', 'Duzenle'),
    ('Admin', 'Personel Hijyen', 'Duzenle'),
    ('Admin', 'Temizlik Kontrol', 'Duzenle'),
    ('Admin', 'Raporlama', 'Duzenle'),
    ('Admin', 'Ayarlar', 'Duzenle')
]

for yetki in yetkiler:
    cursor.execute('INSERT OR IGNORE INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES (?, ?, ?)', yetki)

conn.commit()
conn.close()

print('Basarili!')
print('5 rol eklendi')
print('7 bolum eklendi')
print('6 Admin yetkisi tanimlandi')
