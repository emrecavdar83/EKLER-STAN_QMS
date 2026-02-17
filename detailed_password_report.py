"""
Detaylı Şifre Raporu
====================
Tüm kullanıcıların şifrelerini karşılaştırır.
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
print("DETAYLI ŞİFRE RAPORU (TÜM KULLANICILAR)")
print("="*80)

# Lokaldeki kullanıcılar
local_df = pd.read_sql("""
    SELECT 
        id, 
        ad_soyad,
        kullanici_adi,
        sifre,
        rol
    FROM personel 
    WHERE kullanici_adi IS NOT NULL 
      AND kullanici_adi != ''
    ORDER BY id
""", local_engine)

# Canlıdaki kullanıcılar
live_df = pd.read_sql("""
    SELECT 
        id, 
        ad_soyad,
        kullanici_adi,
        sifre,
        rol
    FROM personel 
    WHERE kullanici_adi IS NOT NULL 
      AND kullanici_adi != ''
    ORDER BY id
""", live_engine)

print(f"\nLokal kullanıcı sayısı: {len(local_df)}")
print(f"Canlı kullanıcı sayısı: {len(live_df)}")

# Karşılaştırma
diff_users = []
missing_in_live = []
password_mismatch = []

for _, local_row in local_df.iterrows():
    user_id = local_row['id']
    live_row = live_df[live_df['id'] == user_id]
    
    if live_row.empty:
        missing_in_live.append({
            'id': user_id,
            'ad_soyad': local_row['ad_soyad'],
            'kullanici_adi': local_row['kullanici_adi'],
            'sifre': local_row['sifre']
        })
    else:
        local_pass = str(local_row['sifre']) if pd.notna(local_row['sifre']) else ""
        live_pass = str(live_row.iloc[0]['sifre']) if pd.notna(live_row.iloc[0]['sifre']) else ""
        
        if local_pass != live_pass:
            password_mismatch.append({
                'id': user_id,
                'ad_soyad': local_row['ad_soyad'],
                'kullanici_adi': local_row['kullanici_adi'],
                'lokal_sifre': local_pass,
                'canli_sifre': live_pass
            })

print("\n" + "="*80)
print("SONUÇLAR")
print("="*80)

if missing_in_live:
    print(f"\n❌ CANLIDA OLMAYAN KULLANICILAR ({len(missing_in_live)}):")
    for user in missing_in_live:
        print(f"   ID {user['id']:3d}: {user['ad_soyad']:30s} | {user['kullanici_adi']:20s} | Şifre: {user['sifre']}")
else:
    print("\n✅ Tüm kullanıcılar canlıda mevcut")

if password_mismatch:
    print(f"\n⚠️ ŞİFRESİ FARKLI KULLANICILAR ({len(password_mismatch)}):")
    for user in password_mismatch:
        print(f"   ID {user['id']:3d}: {user['ad_soyad']:30s}")
        print(f"      Lokal: '{user['lokal_sifre']}'")
        print(f"      Canlı: '{user['canli_sifre']}'")
else:
    print("\n✅ Tüm şifreler eşleşiyor") 

print("\n" + "="*80)
print(f"ÖZET: {len(missing_in_live)} eksik, {len(password_mismatch)} şifre uyumsuz")
print("="*80)
