import sqlite3
import sys

def safe_print(s):
    try:
        print(s.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding))
    except:
        print(s.encode('ascii', errors='replace').decode('ascii'))

conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()

cursor.execute("SELECT id, ad_soyad, pozisyon_seviye FROM personel WHERE departman_id = 23")
safe_print(f"RULO PASTA (ID 23) Personeli: {cursor.fetchall()}")

cursor.execute("SELECT id, ad_soyad, pozisyon_seviye, departman_id FROM personel WHERE ad_soyad LIKE '%MIHRIBAN%' OR ad_soyad LIKE '%MEHRIBAN%'")
safe_print(f"Mihriban Arama: {cursor.fetchall()}")

conn.close()
