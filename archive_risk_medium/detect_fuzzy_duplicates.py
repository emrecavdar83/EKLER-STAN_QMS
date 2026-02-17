import sqlite3
from collections import Counter
import re

def normalize_name(name):
    if not name: return ""
    # Remove numbers, extra spaces, and convert to uppercase
    name = re.sub(r'\d+', '', name)
    name = " ".join(name.split())
    return name.upper()

conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()

cursor.execute("SELECT id, ad_soyad, departman_id, gorev, durum FROM personel WHERE durum = 'AKTİF'")
rows = cursor.fetchall()

name_map = {}
for r in rows:
    norm = normalize_name(r[1])
    if norm not in name_map:
        name_map[norm] = []
    name_map[norm].append(r)

print("--- Potansiyel Mükerrer Kayıtlar (İsim Bazlı) ---")
duplicate_count = 0
for norm, records in name_map.items():
    if len(records) > 1:
        duplicate_count += 1
        print(f"\nİsim Grubu: {norm} ({len(records)} kayıt)")
        for r in records:
            print(f"  ID: {r[0]}, Ad: {r[1]}, Dept: {r[2]}, Görev: {r[3]}")

print(f"\nToplam Mükerrer İsim Grubu: {duplicate_count}")
print(f"Toplam Aktif Personel: {len(rows)}")

conn.close()
