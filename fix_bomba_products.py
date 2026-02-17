# -*- coding: utf-8 -*-
"""
BOMBA Departmanı için ürün görünürlük düzeltmesi
"""
import pandas as pd
from sqlalchemy import create_engine, text
import toml

secrets = toml.load('.streamlit/secrets.toml')
url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
url = url.strip('"')
engine = create_engine(url, pool_pre_ping=True)

print("=== BOMBA DEPARTMANI ÜRÜN DÜZELTMESİ ===\n")

# Mevcut BOMBA ürünlerini göster
print("--- Mevcut BOMBA Ürünleri ---")
df = pd.read_sql(text("SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler WHERE sorumlu_departman ILIKE :p"), 
                 engine, params={"p": "%BOMBA%"})
print(df.to_string(index=False) if not df.empty else "BOMBA ürünü yok!")

# BOMBA ürünlerinin sorumlu_departman değerini sadece 'BOMBA' olarak güncelle
print("\n--- Düzeltme Uygulanıyor ---")
with engine.begin() as conn:
    result = conn.execute(text(
        "UPDATE ayarlar_urunler SET sorumlu_departman = 'BOMBA' WHERE sorumlu_departman ILIKE :p"
    ), {"p": "%BOMBA%"})
    print(f"Güncellenen: {result.rowcount} ürün")

# Düzeltme sonrası
print("\n--- Düzeltme Sonrası ---")
df2 = pd.read_sql(text("SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler WHERE sorumlu_departman ILIKE :p"), 
                  engine, params={"p": "%BOMBA%"})
print(df2.to_string(index=False) if not df2.empty else "BOMBA ürünü yok!")

# Tüm ürün dağılımını göster
print("\n--- Tüm Ürünler ---")
all_products = pd.read_sql("SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler ORDER BY sorumlu_departman", engine)
print(all_products.to_string(index=False))

print("\n✅ Düzeltme tamamlandı!")
