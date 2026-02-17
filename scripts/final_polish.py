import sqlite3

def final_polish():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    # Vardiya Standartlaştırma
    conv = {
        'Gündüz Vardiyası': 'GÜNDÜZ VARDİYASI',
        'Ara Vardiya': 'ARA VARDİYA',
        'Gece Vardiyası': 'GECE VARDİYASI'
    }
    for old, new in conv.items():
        cursor.execute("UPDATE personel SET vardiya = ? WHERE vardiya = ?", (new, old))
        if cursor.rowcount > 0:
            print(f"Vardiya düzeltildi: {old} -> {new}")

    # Mustafa Avşar Fix
    cursor.execute("UPDATE personel SET vardiya = NULL WHERE ad_soyad = 'MUSTAFA AVŞAR'")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    final_polish()
