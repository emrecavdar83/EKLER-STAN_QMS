import sqlite3

def list_active():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    print("--- AKTİF PERSONEL LİSTESİ ---")
    cursor.execute("SELECT id, ad_soyad, bolum, vardiya FROM personel WHERE durum = 'AKTİF' ORDER BY ad_soyad")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
    
    print(f"\nToplam: {len(rows)}")
    conn.close()

if __name__ == "__main__":
    list_active()
