"""
Ürün-Bölüm Eşleştirme Kontrolü
================================
Lokal ve canlı veritabanlarındaki ürün-bölüm eşleştirmelerini karşılaştırır.
"""

import pandas as pd
from sqlalchemy import create_engine
import toml

# Engines
local_engine = create_engine('sqlite:///ekleristan_local.db')
secrets = toml.load('.streamlit/secrets.toml')
live_url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
live_engine = create_engine(live_url, pool_pre_ping=True)

print("="*80)
print("ÜRÜN-BÖLÜM EŞLEŞTİRME KONTROLÜ")
print("="*80)

# 1. Ürünler tablosu
print("\n1️⃣ ÜRÜNLER TABLOSU")
print("-"*80)

local_urunler = pd.read_sql("""
    SELECT u.urun_adi, u.departman_id, b.bolum_adi
    FROM ayarlar_urunler u
    LEFT JOIN tanim_bolumler b ON u.departman_id = b.id
    ORDER BY u.urun_adi
""", local_engine)

live_urunler = pd.read_sql("""
    SELECT u.urun_adi, u.departman_id, b.bolum_adi
    FROM ayarlar_urunler u
    LEFT JOIN tanim_bolumler b ON u.departman_id = b.id
    ORDER BY u.urun_adi
""", live_engine)

print(f"Lokal: {len(local_urunler)} ürün")
print(f"Canlı: {len(live_urunler)} ürün")

# Departman ID'si NULL olan ürünler
local_null = local_urunler[local_urunler['departman_id'].isna()]
live_null = live_urunler[live_urunler['departman_id'].isna()]

print(f"\nDepartman ID'si NULL olanlar:")
print(f"  Lokal: {len(local_null)} ürün")
print(f"  Canlı: {len(live_null)} ürün")

if len(live_null) > 0:
    print("\n⚠️ Canlıda departman ID'si NULL olan ürünler:")
    print(live_null[['urun_adi']].to_string(index=False))

# 2. Bölümler tablosu
print("\n\n2️⃣ BÖLÜMLER TABLOSU")
print("-"*80)

local_bolumler = pd.read_sql("SELECT id, bolum_adi FROM tanim_bolumler ORDER BY id", local_engine)
live_bolumler = pd.read_sql("SELECT id, bolum_adi FROM tanim_bolumler ORDER BY id", live_engine)

print(f"Lokal: {len(local_bolumler)} bölüm")
print(f"Canlı: {len(live_bolumler)} bölüm")

# ID eşleşme kontrolü
local_ids = set(local_bolumler['id'].tolist())
live_ids = set(live_bolumler['id'].tolist())

if local_ids != live_ids:
    print("\n⚠️ Bölüm ID'leri farklı!")
    missing_in_live = local_ids - live_ids
    missing_in_local = live_ids - local_ids
    if missing_in_live:
        print(f"  Canlıda eksik ID'ler: {missing_in_live}")
    if missing_in_local:
        print(f"  Lokalde eksik ID'ler: {missing_in_local}")

# 3. Personel-Bölüm eşleştirmesi
print("\n\n3️⃣ PERSONEL-BÖLÜM EŞLEŞTİRMESİ")
print("-"*80)

local_personel = pd.read_sql("""
    SELECT ad_soyad, rol, departman_id, b.bolum_adi
    FROM personel p
    LEFT JOIN tanim_bolumler b ON p.departman_id = b.id
    WHERE rol LIKE '%SORUMLU%'
    ORDER BY ad_soyad
""", local_engine)

live_personel = pd.read_sql("""
    SELECT ad_soyad, rol, departman_id, b.bolum_adi
    FROM personel p
    LEFT JOIN tanim_bolumler b ON p.departman_id = b.id
    WHERE rol LIKE '%SORUMLU%'
    ORDER BY ad_soyad
""", live_engine)

print(f"Lokal sorumlu sayısı: {len(local_personel)}")
print(f"Canlı sorumlu sayısı: {len(live_personel)}")

# NULL departman kontrolü
local_null_dept = local_personel[local_personel['departman_id'].isna()]
live_null_dept = live_personel[live_personel['departman_id'].isna()]

if len(live_null_dept) > 0:
    print(f"\n⚠️ Canlıda departman ID'si NULL olan sorumlular ({len(live_null_dept)}):")
    print(live_null_dept[['ad_soyad', 'rol']].to_string(index=False))

# Özet
print("\n" + "="*80)
print("ÖZET")
print("="*80)

issues = []
if len(live_null) > 0:
    issues.append(f"{len(live_null)} ürünün departman_id'si NULL")
if len(live_null_dept) > 0:
    issues.append(f"{len(live_null_dept)} sorumlu personelin departman_id'si NULL")
if local_ids != live_ids:
    issues.append("Bölüm ID'leri lokal ve canlıda farklı")

if issues:
    print("\n⚠️ TESPİT EDİLEN SORUNLAR:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
    print("\nÖNERİ: ayarlar_urunler ve tanim_bolumler tablolarını sync edin.")
else:
    print("\n✅ Veri tutarlılığı sorun yok!")
