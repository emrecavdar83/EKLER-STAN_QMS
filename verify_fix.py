# -*- coding: utf-8 -*-
"""Düzeltme sonrası doğrulama"""
import pandas as pd
from sqlalchemy import create_engine
import toml

# Bağlantılar
local_engine = create_engine('sqlite:///ekleristan_local.db', connect_args={'check_same_thread': False})
secrets = toml.load('.streamlit/secrets.toml')
live_url = (secrets.get('DB_URL') or secrets['streamlit']['DB_URL']).strip('"')
live_engine = create_engine(live_url, pool_pre_ping=True)

print("=" * 60)
print("DÜZELTME SONRASI DOĞRULAMA")
print("=" * 60)

for name, engine in [("LOKAL", local_engine), ("CANLI", live_engine)]:
    print(f"\n--- {name} VERİTABANI ---")
    try:
        df = pd.read_sql("SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler ORDER BY sorumlu_departman", engine)
        print(f"Toplam ürün: {len(df)}")
        
        # Hala hiyerarşik olan var mı?
        hier = df[df['sorumlu_departman'].fillna('').str.contains('>', na=False)]
        if not hier.empty:
            print(f"⚠️ Hala hiyerarşik: {len(hier)}")
        else:
            print("✅ Hiyerarşik kayıt kalmadı!")
        
        # Departman dağılımı
        print("\nDepartman Dağılımı:")
        for dept, count in df['sorumlu_departman'].fillna('(BOŞ)').value_counts().items():
            print(f"  {dept:20}: {count} ürün")
    except Exception as e:
        print(f"HATA: {e}")

print("\n" + "=" * 60)
