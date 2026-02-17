import sqlite3

def add_missing():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    # Master Listeden seçilen eksikler (Mükerrerlikten kaçınıldı)
    missing = [
        ('AHMAD KOURANI', 'GENEL TEMİZLİK', 'GÜNDÜZ VARDİYASI', 'HİPODRUM EKMEK FIRINI', '5065866122'),
        ('EZEL ALRIHANI', 'PATAŞU', 'ARA VARDİYA', 'YEŞİLYAYLA CAMİİ', ''),
        ('HAVVA ILBUS', 'KREMA', 'GÜNDÜZ VARDİYASI', '', ''),
        ('NACIYE', 'KREMA', 'GÜNDÜZ VARDİYASI', '', '')
    ]

    for name, dept, vardiya, servis, tel in missing:
        cursor.execute("SELECT id FROM personel WHERE ad_soyad = ?", (name,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO personel (ad_soyad, bolum, vardiya, servis_duragi, telefon_no, durum, pozisyon_seviye, rol, gorev) 
                VALUES (?, ?, ?, ?, ?, 'AKTİF', 5, 'Personel', ?)
            """, (name, dept, vardiya, servis, tel, f"{dept} Personel"))
            print(f"Eklendi: {name}")
        else:
            print(f"Zaten mevcut: {name}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_missing()
