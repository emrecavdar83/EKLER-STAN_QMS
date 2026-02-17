# -*- coding: utf-8 -*-
"""
Ürün Departman Ataması Düzeltme Scripti
- RULO PASTA ürünlerini RULO PASTA departmanına atar
- Diğer eksik atamalar tespit edilir
"""
import os
import pandas as pd
from sqlalchemy import create_engine, text

os.chdir(r"c:\Projeler\S_program\EKLERİSTAN_QMS")

# Lokal SQLite
LOCAL_DB = 'sqlite:///ekleristan_local.db'
engine = create_engine(LOCAL_DB, connect_args={'check_same_thread': False})

print("=== ÜRÜN DEPARTMAN ATAMASI DÜZELTMESİ ===\n")

# Mevcut ürünleri göster
df = pd.read_sql("SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler", engine)
print(f"Düzeltme öncesi: {len(df)} ürün\n")

# Düzeltmeleri uygula
updates = [
    # RULO PASTA ürünleri
    ("RULO PASTA MUZ DOLDUGULU", "RULO PASTA"),
    ("RULO PASTA ÇİKOLATALI", "RULO PASTA"),
]

with engine.connect() as conn:
    for urun_adi, departman in updates:
        sql = text("UPDATE ayarlar_urunler SET sorumlu_departman = :dept WHERE urun_adi = :urun")
        result = conn.execute(sql, {"dept": departman, "urun": urun_adi})
        print(f"  [{result.rowcount} satır] {urun_adi} -> {departman}")
    conn.commit()

print("\n=== DÜZELTME SONRASI DURUM ===")
df_after = pd.read_sql("SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler", engine)
for _, row in df_after.iterrows():
    dept = row['sorumlu_departman'] if pd.notna(row['sorumlu_departman']) else "(BOŞ)"
    print(f"  {row['urun_adi']:35} -> {dept}")

print("\n✅ Lokal düzeltmeler tamamlandı!")
print("\n⚠️ Canlı veritabanına senkronize etmek için sync scriptini çalıştırın.")
