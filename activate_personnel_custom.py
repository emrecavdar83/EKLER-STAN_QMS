import sqlite3

names_to_activate = [
    "BATIKAN ARSLAN",
    "HURMA DENLİYEVA",
    "YELİZ ÇAKIR"
]

def activate_personnel():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    for name in names_to_activate:
        cursor.execute("UPDATE personel SET durum = 'Aktif' WHERE UPPER(ad_soyad) = ?", (name,))
        print(f"{name} durumu 'Aktif' olarak güncellendi.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    activate_personnel()
