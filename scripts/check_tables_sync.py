import sqlite3
import sys

def check():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("\n--- ARAMA SONUÇLARI ---")
    cursor.execute("SELECT id, ad_soyad, bolum, durum FROM personel WHERE ad_soyad LIKE 'AHMAD%' OR ad_soyad LIKE 'MUHAMMED%' OR ad_soyad LIKE 'MOHAMED%'")
    for row in cursor.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    check()
