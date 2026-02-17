"""
Tablo Şema Karşılaştırması
==========================
Lokal ve canlı veritabanlarındaki kritik tabloların sütunlarını karşılaştırır.
"""

import pandas as pd
from sqlalchemy import create_engine, inspect
import toml

# Engines
local_engine = create_engine('sqlite:///ekleristan_local.db')
secrets = toml.load('.streamlit/secrets.toml')
live_url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
live_engine = create_engine(live_url, pool_pre_ping=True)

print("="*80)
print("TABLO ŞEMA KARŞILAŞTIRMASI")
print("="*80)

tables = [
    'ayarlar_urunler',
    'tanim_bolumler',
    'personel',
    'ayarlar_yetkiler'
]

for table in tables:
    print(f"\n{'='*80}")
    print(f"📊 {table.upper()}")
    print('='*80)
    
    try:
        # Lokal şema
        local_df = pd.read_sql(f"SELECT * FROM {table} LIMIT 1", local_engine)
        local_cols = set(local_df.columns)
        
        # Canlı şema
        live_df = pd.read_sql(f"SELECT * FROM {table} LIMIT 1", live_engine)
        live_cols = set(live_df.columns)
        
        print(f"\nLokal sütunlar ({len(local_cols)}):")
        print(f"  {', '.join(sorted(local_cols))}")
        
        print(f"\nCanlı sütunlar ({len(live_cols)}):")
        print(f"  {', '.join(sorted(live_cols))}")
        
        # Farklar
        missing_in_live = local_cols - live_cols
        missing_in_local = live_cols - local_cols
        
        if missing_in_live or missing_in_local:
            print(f"\n⚠️ FARKLAR:")
            if missing_in_live:
                print(f"  Canlıda eksik: {', '.join(sorted(missing_in_live))}")
            if missing_in_local:
                print(f"  Lokalde eksik: {', '.join(sorted(missing_in_local))}")
        else:
            print(f"\n✅ Sütunlar eşleşiyor")
            
    except Exception as e:
        print(f"❌ Hata: {e}")

print("\n" + "="*80)
