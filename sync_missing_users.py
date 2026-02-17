"""
Eksik Kullanıcıları Sync Et
============================
Lokalde olup canlıda olmayan kullanıcıları bulur ve sync eder.
"""

import pandas as pd
from sqlalchemy import create_engine, text
import toml

# Engines
local_engine = create_engine('sqlite:///ekleristan_local.db')
secrets = toml.load('.streamlit/secrets.toml')
live_url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
live_engine = create_engine(live_url, pool_pre_ping=True)

print("="*60)
print("EKSİK KULLANICILAR SYNC")
print("="*60)

# Lokaldeki tüm kullanıcıları al
local_df = pd.read_sql("""
    SELECT * FROM personel 
    WHERE kullanici_adi IS NOT NULL 
      AND kullanici_adi != ''
    ORDER BY id
""", local_engine)

# Canlıdaki kullanıcıları al
live_df = pd.read_sql("""
    SELECT id FROM personel 
    WHERE kullanici_adi IS NOT NULL 
      AND kullanici_adi != ''
""", live_engine)

live_ids = set(live_df['id'].tolist())

missing_users = []
for _, row in local_df.iterrows():
    if row['id'] not in live_ids:
        missing_users.append(row.to_dict())

print(f"\nLokalde olan ama canlıda olmayan: {len(missing_users)} kullanıcı")

if missing_users:
    for user in missing_users:
        print(f"  - ID {user['id']}: {user['ad_soyad']} ({user['kullanici_adi']})")
    
    confirm = input("\nBu kullanıcıları canlıya eklemek ister misiniz? (e/h): ")
    
    if confirm.lower() == 'e':
        with live_engine.begin() as conn:
            missing_df = pd.DataFrame(missing_users)
            # NaN değerleri None yap
            missing_df = missing_df.where(pd.notnull(missing_df), None)
            missing_df.to_sql('personel', conn, if_exists='append', index=False)
            print(f"\n✅ {len(missing_users)} kullanıcı canlıya eklendi!")
    else:
        print("\nİşlem iptal edildi.")
else:
    print("\n✅ Tüm kullanıcılar senkron!")
