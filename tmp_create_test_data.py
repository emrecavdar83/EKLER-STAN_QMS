import sqlite3
from datetime import datetime, timedelta

def generate_test_data():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    print("--- TEST VERİSİ ÜRETİCİSİ (SADECE LOKAL) ---")
    
    bugun = datetime.now()
    bugun_str = bugun.strftime('%Y-%m-%d')
    bas_saat = bugun.replace(hour=8, minute=0, second=0, microsecond=0)
    
    # Odaları al
    cursor.execute("SELECT id, min_sicaklik, max_sicaklik FROM soguk_odalar WHERE aktif=1 LIMIT 2")
    rooms = cursor.fetchall()
    if not rooms:
        print("Hiç oda bulunamadı!")
        return
        
    oda_id1 = rooms[0][0]
    min_s = float(rooms[0][1]) if rooms[0][1] else 0.0
    max_s = float(rooms[0][2]) if rooms[0][2] else 4.0
    
    # Test 1: Sabah 8'de düzgün ölçüm (Planlı)
    zaman1 = bas_saat.strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        INSERT INTO sicaklik_olcumleri 
        (oda_id, sicaklik_degeri, olcum_zamani, planlanan_zaman, kaydeden_kullanici, sapma_var_mi, olusturulma_tarihi)
        VALUES (?, ?, ?, ?, ?, 0, ?)
    """, (oda_id1, (min_s + max_s)/2, zaman1, zaman1, "Test Kullanıcısı 1", zaman1))
    
    olcum1_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO olcum_plani (oda_id, beklenen_zaman, gerceklesen_olcum_id, durum)
        VALUES (?, ?, ?, 'TAMAMLANDI')
    """, (oda_id1, zaman1, olcum1_id))

    # Test 2: Öğlen 12'de SAPMA (Planlı)
    bas_saat = bugun.replace(hour=12, minute=0, second=0, microsecond=0)
    zaman2 = bas_saat.strftime('%Y-%m-%d %H:%M:%S')
    kesin_saat = bugun.replace(hour=12, minute=15, second=0).strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute("""
        INSERT INTO sicaklik_olcumleri 
        (oda_id, sicaklik_degeri, olcum_zamani, planlanan_zaman, kaydeden_kullanici, sapma_var_mi, sapma_aciklamasi, olusturulma_tarihi)
        VALUES (?, ?, ?, ?, ?, 1, 'Limit aşıldı', ?)
    """, (oda_id1, max_s + 4.5, kesin_saat, zaman2, "Test Kullanıcısı 1", kesin_saat))
    
    olcum2_id = cursor.lastrowid
    cursor.execute("""
        INSERT INTO olcum_plani (oda_id, beklenen_zaman, gerceklesen_olcum_id, durum)
        VALUES (?, ?, ?, 'TAMAMLANDI')
    """, (oda_id1, zaman2, olcum2_id))
    
    # Test 3: Öğlen 12:45'te MANUEL DÖF/TAKİP ölçümü (Plansız)
    takip_saat = bugun.replace(hour=12, minute=45, second=0).strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute("""
        INSERT INTO sicaklik_olcumleri 
        (oda_id, sicaklik_degeri, olcum_zamani, kaydeden_kullanici, sapma_var_mi, olusturulma_tarihi)
        VALUES (?, ?, ?, ?, 0, ?)
    """, (oda_id1, (min_s + max_s)/2, takip_saat, "Test Kullanıcısı 1", takip_saat))
    
    conn.commit()
    conn.close()
    print("✅ Başarıyla 3 adet test verisi (Uygun, Sapma ve DÖF/Takip Ölçümü) eklendi.")
    print("Lütfen sayfayı yenileyip Raporu Oluştur butonuna tekrar basınız.")

if __name__ == "__main__":
    generate_test_data()
