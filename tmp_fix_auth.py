import sqlite3

def apply_fix():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    # Modül adı
    modul = 'Soğuk Oda'
    
    # Roller ve yetkileri
    yetkiler = [
        ('PERSONEL', 'YOK'),
        ('KALİTE SORUMLSU', 'DÜZENLE'),
        ('VARDIYA AMIRI', 'DÜZENLE'),
        ('ADMIN', 'Düzenle'),
        ('BÖLÜM SORUMLUSU', 'Düzenle'),
        ('GENEL KOORDİNATÖR', 'Düzenle'),
        ('GENEL MÜDÜR', 'Görüntüle'),
        ('PLANLAMA YÖNETİCİSİ', 'Görüntüle'),
        ('ÜRETİM MÜDÜRÜ', 'Görüntüle')
    ]
    
    # Mevcutları kontrol et (varsa silip tekrar ekle garantici olmak için)
    cursor.execute("DELETE FROM ayarlar_yetkiler WHERE modul_adi = ?", (modul,))
    
    # Ekle
    for rol, yetki in yetkiler:
        cursor.execute("INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) VALUES (?, ?, ?)", (rol, modul, yetki))
        print(f"Added: {rol} -> {modul} ({yetki})")
    
    conn.commit()
    conn.close()
    print("Fix applied successfully.")

if __name__ == "__main__":
    apply_fix()
