# -*- coding: utf-8 -*-
"""
yeliz.cakır kullanıcısının ürün görünürlük sorunu analizi
"""
import pandas as pd
from sqlalchemy import create_engine, text
import toml

# Secrets dosyasından bağlantı bilgisi al
secrets = toml.load('.streamlit/secrets.toml')
live_url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
if live_url.startswith('"') and live_url.endswith('"'):
    live_url = live_url[1:-1]
live_engine = create_engine(live_url, pool_pre_ping=True)

print("=== YELİZ ÇAKIR - ÜRÜN GÖRÜNÜRLÜK ANALİZİ ===\n")

# 1. Kullanıcı bilgilerini al
print("--- 1. KULLANICI BİLGİLERİ ---")
user_df = pd.read_sql(text("""
    SELECT p.id, p.ad_soyad, p.kullanici_adi, p.rol, p.bolum, p.departman_id, 
           d.bolum_adi as departman_adi
    FROM personel p
    LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
    WHERE LOWER(p.kullanici_adi) LIKE :pattern OR LOWER(p.ad_soyad) LIKE :pattern
"""), live_engine, params={"pattern": "%yeliz%"})

if user_df.empty:
    print("⚠️ yeliz kullanıcısı bulunamadı!")
else:
    print(user_df.to_string(index=False))
    
    user_bolum = user_df.iloc[0]['bolum'] or user_df.iloc[0]['departman_adi']
    user_rol = user_df.iloc[0]['rol']
    print(f"\n→ Bölüm: {user_bolum}")
    print(f"→ Rol: {user_rol}")

# 2. Tüm ürünleri ve departman atamalarını göster
print("\n--- 2. TÜM ÜRÜNLER VE DEPARTMAN ATAMALARI ---")
products_df = pd.read_sql("""
    SELECT urun_adi, sorumlu_departman 
    FROM ayarlar_urunler 
    ORDER BY sorumlu_departman, urun_adi
""", live_engine)
print(products_df.to_string(index=False))

# 3. Departman dağılımı
print("\n--- 3. DEPARTMAN DAĞILIMI ---")
dept_counts = products_df['sorumlu_departman'].fillna('(BOŞ)').value_counts()
for dept, count in dept_counts.items():
    print(f"  {dept:30}: {count} ürün")

# 4. Kullanıcının görmesi gereken ürünler
if not user_df.empty and user_bolum:
    print(f"\n--- 4. {user_bolum} BÖLÜMÜ İÇİN ÜRÜNLER ---")
    # Filtreleme mantığı: sorumlu_departman içinde user_bolum geçenler VEYA boş olanlar
    matching = products_df[
        products_df['sorumlu_departman'].fillna('').str.contains(str(user_bolum), case=False, na=False) |
        products_df['sorumlu_departman'].isna() |
        (products_df['sorumlu_departman'] == '')
    ]
    if matching.empty:
        print(f"⚠️ {user_bolum} bölümü için eşleşen ürün YOK!")
        print(f"\n💡 ÇÖZÜM: Ürünlere '{user_bolum}' departmanı atanmalı veya genel ürünler eklenmeli.")
    else:
        print(matching.to_string(index=False))

print("\n✅ Analiz tamamlandı.")
