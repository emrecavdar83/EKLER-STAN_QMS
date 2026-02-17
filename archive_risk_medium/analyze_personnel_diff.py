import sqlite3
import re

def normalize_name(name):
    if not name: return ""
    name = re.sub(r'\d+', '', name)
    name = " ".join(name.split())
    return name.upper()

# 1. Parse raw data
master_names = []
with open('raw_personnel_data.txt', 'r', encoding='utf-8') as f:
    for line in f:
        match = re.match(r'^\d+\s+(.*?)\s+(?:PROFİTEROL|PANDİSPANYA|FIRIN|GENEL TEMİZLİK|KREMA|BOMBA|SOS|RULO PASTA|DEPO|HALKA TATLI|BULAŞIKHANE|EKİP SORUMLUSU|SEVKİYAT|BAKIM|SNOWLAND|İ\.K\.|İDARİ PERSONEL|GIDA MÜH\.|KALİTE MÜDÜRÜ)', line)
        if match:
            master_names.append(match.group(1).strip())

print(f"Master Listeden okunan isim sayısı: {len(master_names)}")

# 2. Check local DB
conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()

cursor.execute("SELECT id, ad_soyad FROM personel WHERE durum = 'AKTİF'")
local_active = cursor.fetchall()

print(f"Lokal AKTİF sayısı: {len(local_active)}")

# Identify extras
local_active_names = {r[1].upper(): r[0] for r in local_active}
master_names_upper = [n.upper() for n in master_names]

extras = []
for name, pid in local_active_names.items():
    if name not in master_names_upper:
        # Check fuzzy match
        found = False
        for mn in master_names_upper:
            if mn in name or name in mn:
                found = True
                break
        if not found:
            extras.append((pid, name))

print(f"\nMaster listede bulunmayan AKTİF personeller ({len(extras)}):")
for pid, name in extras:
    print(f"  ID: {pid}, Ad: {name}")

conn.close()
