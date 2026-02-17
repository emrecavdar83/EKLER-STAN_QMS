import sqlite3
import pandas as pd

conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()

def fix_ezel():
    print("--- EZEL TEMIZLIK ISLEMI ---")
    
    # 1. Tum EZEL kayitlarini bul
    cursor.execute("SELECT id, ad_soyad, bolum, departman_id FROM personel WHERE ad_soyad LIKE '%EZEL%'")
    rows = cursor.fetchall()
    
    for row in rows:
        print(f"ID: {row[0]} | Isim: {row[1]} | Bolum: {row[2]} | DeptID: {row[3]}")

    # 2. Mukerrerleri Temizle
    # En guncel isim ve veriye sahip 367'yi tutalim, 239 ve 294'u silelim.
    # Onemli: Eger digerlerinde daha iyi veri varsa (bolum vb) onu 367'ye tasiyabiliriz.
    # 294'te servis duragi vardi, onu 367'ye tasiyalim.
    
    cursor.execute("SELECT servis_duragi, telefon_no FROM personel WHERE id = 294")
    extra = cursor.fetchone()
    if extra:
        cursor.execute("UPDATE personel SET servis_duragi = ?, telefon_no = ? WHERE id = 367", extra)
        print("- Ek bilgiler ID 294'ten 367'ye tasindi.")

    cursor.execute("DELETE FROM personel WHERE id IN (239, 294)")
    print("- Mukerrer kayitlar silindi.")
    
    # Ismi standartlastir
    cursor.execute("UPDATE personel SET ad_soyad = 'EZEL ALRIHANI' WHERE id = 367")
    
    # 3. Departman Bilgisini Zorla Duzelt
    # Eger bolum 'PATAŞU' ise departman_id 11 olmali (ayarlar_bolumler tablosuna gore)
    cursor.execute("UPDATE personel SET departman_id = 11, bolum = 'PATAŞU' WHERE id = 367")
    print("- Ezel ALRIHANI departmani PATAŞU (ID:11) olarak set edildi.")

    # 4. Genel Kontrol: Departman ID'si 0 veya NULL olanlari otomatik eslestirmeyi dene
    # fix_org_chart.py'daki mantigi tekrar calistiriyoruz
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
    print(f"- Departman ID eslestirmesi yapildi. {cursor.rowcount} satir guncellendi.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    fix_ezel()
