import sqlite3

conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()

def silent_fix():
    # 1. EZEL ALRIHANI MUKERRER TEMIZLIGI
    # ID 294'teki bilgileri 367'ye tasi (Servis ve Telefon)
    cursor.execute("SELECT servis_duragi, telefon_no FROM personel WHERE id = 294")
    extra = cursor.fetchone()
    if extra:
        cursor.execute("UPDATE personel SET servis_duragi = ?, telefon_no = ? WHERE id = 367", extra)

    # Mukerrerleri sil
    cursor.execute("DELETE FROM personel WHERE id IN (239, 294)")
    
    # Isim ve Departman duzelt (ID 11 = PATAŞU)
    # bolum kolonuna da girintili olmayan temiz hali yazalim
    cursor.execute("UPDATE personel SET ad_soyad = 'EZEL ALRIHANI', departman_id = 11, bolum = 'PATAŞU' WHERE id = 367")
    
    # 2. GENEL DEPARTMAN ID ESLESTIRME (NULL veya 0 kalanlar icin)
    # bolum yazili ama ID atanmamis olanlari yakala
    cursor.execute("""
        UPDATE personel
        SET departman_id = (
            SELECT id 
            FROM ayarlar_bolumler 
            WHERE UPPER(TRIM(replace(bolum_adi, 'I', 'İ'))) = UPPER(TRIM(replace(personel.bolum, 'I', 'İ')))
            LIMIT 1
        )
        WHERE (departman_id IS NULL OR departman_id = 0) AND bolum IS NOT NULL AND bolum != '';
    """)

    conn.commit()
    
    # Kontrol: Hala 0 kalan var mi?
    cursor.execute("SELECT id, ad_soyad, bolum FROM personel WHERE (departman_id IS NULL OR departman_id = 0)")
    remains = cursor.fetchall()
    
    conn.close()
    return remains

if __name__ == "__main__":
    remains = silent_fix()
    if not remains:
        print("BASARILI: Tum personeller departmanlariyla eslesti.")
    else:
        print(f"DIKKAT: {len(remains)} personel hala eslesemedi.")
        for r in remains:
            # Sadece ASCII karakterleri print etmeye calisalim (Hata almamak icin)
            print(f"ID: {r[0]} - Problem: {r[1]}")
