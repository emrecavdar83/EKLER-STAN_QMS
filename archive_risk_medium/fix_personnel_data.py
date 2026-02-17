import sqlite3

def fix_data():
    conn = sqlite3.connect('ekleristan_local.db')
    cur = conn.cursor()
    
    print("Mükerrer personel kayıtları siliniyor...")
    # Ahmad Kourani: ID 7 (Duplicate of 6)
    cur.execute("DELETE FROM personnel WHERE id = 7")
    # Hassan Habra: ID 76 (Duplicate of 75)
    cur.execute("DELETE FROM personnel WHERE id = 76")
    
    print("Mustafa Avşar (ID 112) verisi düzeltiliyor...")
    # Mustafa Avşar'ın vardiya verisini servis durağına taşıyıp vardiyasını standartlaştırıyoruz.
    cur.execute("""
        UPDATE personnel 
        SET servis_duragi = 'KÜÇÜKSANAYİ METRO', 
            vardiya = 'GÜNDÜZ VARDİYASI' 
        WHERE id = 112
    """)
    
    print("Vardiya tanımları sanitize ediliyor...")
    # Bozuk karakterli vardiyaları standartlaştırıyoruz
    replacements = {
        'GNDZ VARDYASI': 'GÜNDÜZ VARDİYASI',
        'ARA VARDYA': 'ARA VARDİYA',
        'GECE VARDYASI': 'GECE VARDİYASI',
        'KKSANAY METRO': 'GÜNDÜZ VARDİYASI' # Diğerleri için de temizlik
    }
    
    for old, new in replacements.items():
        cur.execute("UPDATE personnel SET vardiya = ? WHERE vardiya = ?", (new, old))
    
    # Kalan "?" gibi karakterleri içeren vardiyaları da kontrol edelim (opsiyonel ama güvenli)
    cur.execute("UPDATE personnel SET vardiya = 'GÜNDÜZ VARDİYASI' WHERE vardiya LIKE '%G%ND%Z%'")
    cur.execute("UPDATE personnel SET vardiya = 'ARA VARDİYA' WHERE vardiya LIKE '%ARA%'")
    cur.execute("UPDATE personnel SET vardiya = 'GECE VARDİYASI' WHERE vardiya LIKE '%GECE%'")

    conn.commit()
    
    # Sonuçları kontrol edelim
    cur.execute("SELECT COUNT(*) FROM personnel")
    count = cur.fetchone()[0]
    print(f"\nİşlem Tamamlandı.")
    print(f"Toplam Personel Sayısı: {count}")
    
    conn.close()

if __name__ == "__main__":
    fix_data()
