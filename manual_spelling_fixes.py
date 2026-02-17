import sqlite3

fixes = [
    ("HAMZA ASHRAM", "Hamza Ashran", "BOMBA"),
    ("TELAL ŞAKİFA", "Telal Sefika", "BOMBA"),
    ("ZUBALA MEHDİ", "Zubale Mehti", "RULO PASTA"),
    ("VELİD ALAMRA", "Valid Elamro", "RULO PASTA")
]

conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()

for old, new, dept in fixes:
    cursor.execute("UPDATE personel SET ad_soyad = ?, bolum = ?, durum = 'Aktif' WHERE UPPER(ad_soyad) = ?", (new, dept, old))
    print(f"Fixed {old} -> {new}")

conn.commit()
conn.close()
