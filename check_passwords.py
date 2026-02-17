"""
Şifre Durumu Kontrolü
=====================
Lokal ve canlı veritabanındaki şifreleri karşılaştırır.
"""

import pandas as pd
from sqlalchemy import create_engine
import toml

# Engines
local_engine = create_engine('sqlite:///ekleristan_local.db')
secrets = toml.load('.streamlit/secrets.toml')
live_url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
live_engine = create_engine(live_url, pool_pre_ping=True)

print("="*60)
print("ŞİFRE DURUMU KONTROLÜ")
print("="*60)

# Lokal şifreler
local_query = """
SELECT 
    id, 
    ad_soyad as isim,
    kullanici_adi,
    sifre,
    rol
FROM personel 
WHERE kullanici_adi IS NOT NULL 
  AND kullanici_adi != ''
ORDER BY id
LIMIT 10
"""

print("\n📍 LOKAL VERİTABANI:")
local_df = pd.read_sql(local_query, local_engine)
print(local_df.to_string(index=False))

# Canlı şifreler
print("\n\n📍 CANLI VERİTABANI:")
live_df = pd.read_sql(local_query, live_engine)
print(live_df.to_string(index=False))

# Karşılaştırma
print("\n" + "="*60)
print("FARKLAR")
print("="*60)

diff_count = 0
for _, local_row in local_df.iterrows():
    user_id = local_row['id']
    live_row = live_df[live_df['id'] == user_id]
    
    if live_row.empty:
        print(f"❌ ID {user_id} ({local_row['isim']}): Canlıda yok!")
        diff_count += 1
    else:
        local_pass = str(local_row['sifre']) if pd.notna(local_row['sifre']) else "BOŞ"
        live_pass = str(live_row.iloc[0]['sifre']) if pd.notna(live_row.iloc[0]['sifre']) else "BOŞ"
        
        if local_pass != live_pass:
            print(f"⚠️ ID {user_id} ({local_row['isim']}): Şifre farklı!")
            print(f"   Lokal: {local_pass}")
            print(f"   Canlı: {live_pass}")
            diff_count += 1

if diff_count == 0:
    print("✅ İlk 10 kullanıcının şifreleri eşleşiyor!")
else:
    print(f"\n⚠️ {diff_count} kullanıcıda fark tespit edildi.")
