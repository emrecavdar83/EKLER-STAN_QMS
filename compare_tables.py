"""
Basit Lokal-Canlı Tablo Karşılaştırması
==========================================
Kritik tabloları karşılaştırır ve farkları gösterir.
"""

import pandas as pd
from sqlalchemy import create_engine, text
import toml
import os

# Lokal DB
local_engine = create_engine('sqlite:///ekleristan_local.db')

# Canlı DB - secrets.toml'dan al
secrets_path = '.streamlit/secrets.toml'
secrets = toml.load(secrets_path)
live_url = secrets.get('DB_URL') or secrets.get('streamlit', {}).get('DB_URL')
live_engine = create_engine(live_url, pool_pre_ping=True)

# Kontrol edilecek kritik tablolar
CRITICAL_TABLES = [
    'ayarlar_roller',
    'ayarlar_yetkiler', 
    'tanim_bolumler',
    'ayarlar_urunler',
    'personel'
]

def compare_table(table_name):
    """Tablo karşılaştırması yapar."""
    print(f"\n{'='*60}")
    print(f"📊 {table_name.upper()}")
    print('='*60)
    
    try:
        # Lokal veri
        local_df = pd.read_sql(f"SELECT * FROM {table_name}", local_engine)
        print(f"Lokal: {len(local_df)} satır")
        
        # Canlı veri
        live_df = pd.read_sql(f"SELECT * FROM {table_name}", live_engine)
        print(f"Canlı: {len(live_df)} satır")
        
        # Satır sayısı farkı
        diff = len(local_df) - len(live_df)
        if diff > 0:
            print(f"⚠️ Lokal {diff} satır fazla (yeni kayıtlar var)")
        elif diff < 0:
            print(f"⚠️ Canlı {-diff} satır fazla (lokal eksik)")
        else:
            print("✅ Satır sayıları eşit")
            
        # Sütun karşılaştırması
        local_cols = set(local_df.columns)
        live_cols = set(live_df.columns)
        
        if local_cols != live_cols:
            print(f"\n⚠️ Sütun farkı var:")
            missing_in_live = local_cols - live_cols
            missing_in_local = live_cols - local_cols
            if missing_in_live:
                print(f"  Canlıda eksik: {missing_in_live}")
            if missing_in_local:
                print(f"  Lokalde eksik: {missing_in_local}")
        else:
            print("✅ Sütunlar eşit")
            
        return {
            'lokal_rows': len(local_df),
            'canli_rows': len(live_df),
            'diff': diff,
            'cols_match': local_cols == live_cols
        }
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        return None

if __name__ == "__main__":
    print("="*60)
    print("LOKAL - CANLI VERİTABANI KARŞILAŞTIRMASI")
    print("="*60)
    
    results = {}
    for table in CRITICAL_TABLES:
        results[table] = compare_table(table)
    
    print(f"\n{'='*60}")
    print("ÖZET")
    print('='*60)
    
    needs_sync = []
    for table, result in results.items():
        if result and result['diff'] != 0:
            needs_sync.append(table)
            
    if needs_sync:
        print(f"\n⚠️ Sync gerekli tablolar: {', '.join(needs_sync)}")
        print("\\nBu tabloları sync etmek için aşağıdaki komutu çalıştırın:")
        print("  python simple_sync.py --tables " + ",".join(needs_sync))
    else:
        print("\\n✅ Tüm kritik tablolar senkron!")
