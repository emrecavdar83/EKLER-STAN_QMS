import pandas as pd
import sqlite3

conn = sqlite3.connect("ekleristan_local.db")
print("\n--- Pozisyon Seviyesi Dagilimi ---")
levels = pd.read_sql("SELECT pozisyon_seviye, count(*) as count FROM personel GROUP BY pozisyon_seviye", conn)
print(levels)

print("\n--- Potansiyel Yoneticiler (< Level 5) ---")
managers = pd.read_sql("SELECT id, ad_soyad, bolum, gorev, pozisyon_seviye FROM personel WHERE pozisyon_seviye < 5", conn)
print(managers)
conn.close()
