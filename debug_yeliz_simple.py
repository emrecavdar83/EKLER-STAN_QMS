# -*- coding: utf-8 -*-
"""Yeliz kullanıcı ve ürün analizi"""
import pandas as pd
from sqlalchemy import create_engine
import toml

secrets = toml.load('.streamlit/secrets.toml')
url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
url = url.strip('"')
engine = create_engine(url, pool_pre_ping=True)

print("=== YELİZ KULLANICI ANALİZİ ===\n")

# Tüm kullanıcıları çek ve yeliz/cakır ara
df = pd.read_sql("SELECT id, ad_soyad, kullanici_adi, rol, bolum, departman_id FROM personel", engine)
print(f"Toplam personel: {len(df)}\n")

# yeliz veya cakir içeren kayıtlar
yeliz = df[df['ad_soyad'].str.contains('yeliz|çakır|cakir', case=False, na=False) | 
           df['kullanici_adi'].str.contains('yeliz|cakir', case=False, na=False)]
print("--- Yeliz/Çakır içeren kayıtlar ---")
print(yeliz.to_string(index=False) if not yeliz.empty else "Bulunamadı!")

# Tüm ürünleri göster
print("\n--- Mevcut Ürünler ---")
products = pd.read_sql("SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler", engine)
print(products.to_string(index=False))
