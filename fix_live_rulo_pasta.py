# -*- coding: utf-8 -*-
"""
Canlı Veritabanı - RULO PASTA Ürün Departman Düzeltmesi
"""
import pandas as pd
from sqlalchemy import create_engine, text
import toml

# Secrets dosyasından bağlantı bilgisi al (aynı yöntem diğer scriptlerle)
secrets = toml.load('.streamlit/secrets.toml')

# URL'yi al - farklı formatlara uyumlu
if 'DB_URL' in secrets:
    live_url = secrets['DB_URL']
elif 'streamlit' in secrets and 'DB_URL' in secrets['streamlit']:
    live_url = secrets['streamlit']['DB_URL']
else:
    raise ValueError("DB_URL bulunamadı")

# Tırnak işaretlerini temizle
if live_url.startswith('"') and live_url.endswith('"'):
    live_url = live_url[1:-1]

live_engine = create_engine(live_url, pool_pre_ping=True)

print("=== CANLI VERİTABANI - RULO PASTA DÜZELTMESİ ===\n")
print("Bağlantı test ediliyor...")

# Bağlantı testi
try:
    with live_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✅ Bağlantı başarılı!\n")
except Exception as e:
    print(f"❌ Bağlantı hatası: {e}")
    exit(1)

# Önce mevcut durumu göster
print("--- Düzeltme ÖNCESİ ---")
try:
    df_before = pd.read_sql(text(
        "SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler WHERE urun_adi ILIKE :pattern"
    ), live_engine, params={"pattern": "%RULO PASTA%"})
    print(df_before.to_string(index=False) if not df_before.empty else "RULO PASTA ürün bulunamadı")
except Exception as e:
    print(f"Kayıt okuma hatası: {e}")
    exit(1)

# Düzeltmeleri uygula
print("\n--- Düzeltme Uygulanıyor ---")
with live_engine.begin() as conn:
    result = conn.execute(text(
        "UPDATE ayarlar_urunler SET sorumlu_departman = 'RULO PASTA' "
        "WHERE urun_adi ILIKE :pattern "
        "AND (sorumlu_departman IS NULL OR sorumlu_departman = '')"
    ), {"pattern": "%RULO PASTA%"})
    print(f"  Güncellenen satır sayısı: {result.rowcount}")

# Düzeltme sonrası durumu göster
print("\n--- Düzeltme SONRASI ---")
df_after = pd.read_sql(text(
    "SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler WHERE urun_adi ILIKE :pattern"
), live_engine, params={"pattern": "%RULO PASTA%"})
print(df_after.to_string(index=False) if not df_after.empty else "RULO PASTA ürün bulunamadı")

print("\n✅ Canlı veritabanında RULO PASTA ürünleri başarıyla düzeltildi!")
