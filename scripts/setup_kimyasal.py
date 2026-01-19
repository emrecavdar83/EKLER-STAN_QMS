import sqlite3

conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()

# Kimyasal envanter tablosu
cursor.execute('''
CREATE TABLE IF NOT EXISTS kimyasal_envanter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    kimyasal_adi TEXT NOT NULL,
    tedarikci TEXT,
    msds_yolu TEXT,
    tds_yolu TEXT,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
''')

# Örnek kimyasal ekle
cursor.execute('''
INSERT OR IGNORE INTO kimyasal_envanter (kimyasal_adi, tedarikci) VALUES 
('Klor Bazlı Dezenfektan', 'Tedarikci A'),
('Yüzey Temizleyici', 'Tedarikci B'),
('El Sabunu', 'Tedarikci C')
''')

conn.commit()
conn.close()

print('Basarili!')
print('Kimyasal tablosu olusturuldu')
print('3 ornek kimyasal eklendi')
