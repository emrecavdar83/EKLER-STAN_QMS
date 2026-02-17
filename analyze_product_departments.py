"""
Ürün-Bölüm Sorumlu Eşleştirme Analizi
======================================
"""

import pandas as pd
from sqlalchemy import create_engine
import toml

local_engine = create_engine('sqlite:///ekleristan_local.db')
secrets = toml.load('.streamlit/secrets.toml')
live_url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
live_engine = create_engine(live_url, pool_pre_ping=True)

print("="*80)
print("ÜRÜN-BÖLÜM SORUMLUSU EŞLEŞTİRME ANALİZİ")
print("="*80)

# Lokal: Ürünler ve sorumlu departmanlar
print("\n📍 LOKAL VERİTABANI")
print("-"*80)
local_df = pd.read_sql("""
    SELECT urun_adi, sorumlu_departman, urun_tipi
    FROM ayarlar_urunler
    WHERE sorumlu_departman IS NOT NULL
    ORDER BY sorumlu_departman, urun_adi
    LIMIT 20
""", local_engine)

print(f"Örnek kayıtlar ({len(local_df)}):")
print(local_df.to_string(index=False))

# Benzersiz departmanlar
local_depts = local_df['sorumlu_departman'].unique()
print(f"\nBenzersiz departmanlar ({len(local_depts)}):")
for dept in sorted(local_depts):
    count = len(local_df[local_df['sorumlu_departman'] == dept])
    print(f"  - {dept}: {count} ürün")

# Canlı: Ürünler ve sorumlu departmanlar
print("\n\n📍 CANLI VERİTABANI")
print("-"*80)
live_df = pd.read_sql("""
    SELECT urun_adi, sorumlu_departman, urun_tipi
    FROM ayarlar_urunler
    WHERE sorumlu_departman IS NOT NULL
    ORDER BY sorumlu_departman, urun_adi
    LIMIT 20
""", live_engine)

print(f"Örnek kayıtlar ({len(live_df)}):")
print(live_df.to_string(index=False))

# Benzersiz departmanlar
live_depts = live_df['sorumlu_departman'].unique()
print(f"\nBenzersiz departmanlar ({len(live_depts)}):")
for dept in sorted(live_depts):
    count = len(live_df[live_df['sorumlu_departman'] == dept])
    print(f"  - {dept}: {count} ürün")

# Karşılaştırma
print("\n" + "="*80)
print("KARŞILAŞTıRMA")
print("="*80)

# Toplam sayılar
local_total = pd.read_sql("SELECT COUNT(*) as count FROM ayarlar_urunler WHERE sorumlu_departman IS NOT NULL", local_engine).iloc[0]['count']
live_total = pd.read_sql("SELECT COUNT(*) as count FROM ayarlar_urunler WHERE sorumlu_departman IS NOT NULL", live_engine).iloc[0]['count']

print(f"\nSorumlu departmanı olan ürünler:")
print(f"  Lokal: {local_total}")
print(f"  Canlı: {live_total}")

if local_total != live_total:
    print(f"\n⚠️ FARK: {abs(local_total - live_total)} ürün")
    if local_total > live_total:
        print("  Lokal daha güncel, sync gerekli!")
else:
    print("\n✅ Ürün sayıları eşit")

# Departman adı farkları
local_set = set(local_depts)
live_set = set(live_depts)

if local_set != live_set:
    print(f"\n⚠️ Departman adları farklı!")
    missing_in_live = local_set - live_set
    missing_in_local = live_set - local_set
    if missing_in_live:
        print(f"  Canlıda eksik: {', '.join(sorted(missing_in_live))}")
    if missing_in_local:
        print(f"  Lokalde eksik: {', '.join(sorted(missing_in_local))}")
