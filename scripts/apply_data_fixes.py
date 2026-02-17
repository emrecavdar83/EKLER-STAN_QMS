import sqlite3

def normalize_name(name):
    if not name: return ""
    return str(name).upper().replace('İ','I').replace('Ğ','G').replace('Ü','U').replace('Ş','S').replace('Ö','O').replace('Ç','C').replace(' ','')

def fix_data():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    print("--- PERSONEL TABLOSU DÜZENLEME BAŞLATILDI ---")
    
    # 1. ENCODING VE STANDARTLAŞTIRMA
    translation_map = {
        'GNDZ VARDYASI': 'GÜNDÜZ VARDİYASI',
        'ARA VARDYA': 'ARA VARDİYA',
        'GECE VARDYASI': 'GECE VARDİYASI',
        'Gündüz Vardiyası': 'GÜNDÜZ VARDİYASI',
        'Ara Vardiya': 'ARA VARDİYA',
        'Gece Vardiyası': 'GECE VARDİYASI',
        'BULAIKHANE': 'BULAŞIKHANE',
        'ET LEME': 'ET İŞLEME',
        'GENEL TEMZLK': 'GENEL TEMİZLİK',
        'KALTE': 'KALİTE',
        'PANDSPANYA': 'PANDİSPANYA',
        'PATAU': 'PATAŞU',
        'PROFTEROL': 'PROFİTEROL',
        'YNETM': 'YÖNETİM',
        'RETM': 'ÜRETİM',
        'NSAN KAYNAKLARI': 'İNSAN KAYNAKLARI'
    }

    # Departman tablosunu düzelt
    for old, new in translation_map.items():
        cursor.execute("UPDATE ayarlar_bolumler SET bolum_adi = ? WHERE bolum_adi = ?", (new, old))

    # Personel tablosundaki kolonları düzelt (Hem 'personel' hem 'personnel')
    for table in ['personel', 'personnel']:
        for old, new in translation_map.items():
            cursor.execute(f"UPDATE {table} SET vardiya = ? WHERE vardiya = ?", (new, old))
            cursor.execute(f"UPDATE {table} SET bolum = ? WHERE bolum = ?", (new, old))

    # Vardiya programını düzelt (Emin olmak için tablo kontrolü ile)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='personel_vardiya_programi'")
    if cursor.fetchone():
        for old, new in translation_map.items():
            cursor.execute("UPDATE personel_vardiya_programi SET vardiya = ? WHERE vardiya = ?", (new, old))

    # 2. MUSTAFA AVŞAR ÖZEL DÜZELTME
    cursor.execute("""
        UPDATE personel 
        SET vardiya = NULL, servis_duragi = 'KÜÇÜKSANAYİ METRO' 
        WHERE ad_soyad = 'MUSTAFA AVŞAR' AND (vardiya = '' OR vardiya IS NULL)
    """)

    # 3. MÜKERRER KAYIT TEMİZLİĞİ (İsim bazlı)
    # Ahmad Kourani ve Hassan Habra'nın personnel tablosundaki durumlarını gördük. 
    # Personel tablosunda da benzerleri varsa temizle.
    names_to_dedupe = ['AHMAD KOURANI', 'HASSAN HABRA']
    for name in names_to_dedupe:
        cursor.execute("SELECT id FROM personel WHERE ad_soyad = ? ORDER BY id", (name,))
        ids = cursor.fetchall()
        if len(ids) > 1:
            main_id = ids[0][0]
            for extra_id in ids[1:]:
                cursor.execute("DELETE FROM personel WHERE id = ?", (extra_id[0],))
                print(f"Personel: {name} mükerrer ID {extra_id[0]} silindi.")

    conn.commit()
    
    # 4. MASTER LİSTE İLE SENKRONİZASYON (PASİF ÇEKME)
    # Master listedeki isimleri al
    master_names = []
    try:
        with open('personnel_update_20260131.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()[1:] # Header atla
            for line in lines:
                parts = line.split('\t')
                if len(parts) > 1:
                    master_names.append(normalize_name(parts[1]))
    except Exception as e:
        print(f"Master liste okunamadı: {e}")

    if master_names:
        cursor.execute("SELECT id, ad_soyad FROM personel WHERE durum = 'AKTİF'")
        db_personnel = cursor.fetchall()
        deactivated = 0
        for pid, name in db_personnel:
            if normalize_name(name) not in master_names:
                cursor.execute("UPDATE personel SET durum = 'PASİF' WHERE id = ?", (pid,))
                deactivated += 1
        print(f"Master listede olmayan {deactivated} kişi pasife çekildi.")

    conn.commit()
    conn.close()
    print("--- DÜZELTME İŞLEMİ TAMAMLANDI ---")

if __name__ == "__main__":
    fix_data()
