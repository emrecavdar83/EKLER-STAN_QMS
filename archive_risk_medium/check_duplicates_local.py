import sqlite3

names_to_check = [
    "AHMAD KOURANI", "HAŞEM ARİF", "ÖZLEM YORDAM", "MOHAMAD MASSAT",
    "ALAA MAHCUB", "TELAL ŞAKİFA", "CELEL EL MAHFUZ", "ABDULKERİM MAĞRİBİ"
]

conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()

print("--- Lokal Veritabanı (personel) Kontrolü ---")
for name in names_to_check:
    cursor.execute("SELECT id, ad_soyad, departman_id, gorev FROM personel WHERE ad_soyad LIKE ?", (f"%{name}%",))
    results = cursor.fetchall()
    print(f"\n{name} ({len(results)} kayıt):")
    for r in results:
        print(f"  ID: {r[0]}, Ad: {r[1]}, Dept ID: {r[2]}, Görev: {r[3]}")

cursor.execute("SELECT COUNT(*) FROM personel WHERE durum = 'AKTİF'")
active_count = cursor.fetchone()[0]
print(f"\nToplam AKTİF Personel Sayısı: {active_count}")

cursor.execute("SELECT COUNT(*) FROM personel")
total_count = cursor.fetchone()[0]
print(f"Toplam Personel Sayısı (Tümü): {total_count}")

conn.close()
