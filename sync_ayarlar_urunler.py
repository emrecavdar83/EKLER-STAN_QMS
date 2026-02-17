"""
ayarlar_urunler Tablosu Sync
==============================
Lokal'deki ayarlar_urunler tablosunu canlıya sync eder.
ÖNEMLİ: Önce sütun kontrolü yapar, gerekirse canlıda sütun ekler.
"""

import pandas as pd
from sqlalchemy import create_engine, text
import toml

local_engine = create_engine('sqlite:///ekleristan_local.db')
secrets = toml.load('.streamlit/secrets.toml')
live_url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
live_engine = create_engine(live_url, pool_pre_ping=True)

print("="*80)
print("AYARLAR_URUNLER TABLOSU SYNC")
print("="*80)

# 1. Sütun kontrolü
print("\n1️⃣ SÜTUN KONTROLÜ")
print("-"*80)

local_df = pd.read_sql("SELECT * FROM ayarlar_urunler LIMIT 1", local_engine)
live_df = pd.read_sql("SELECT * FROM ayarlar_urunler LIMIT 1", live_engine)

local_cols = set(local_df.columns)
live_cols = set(live_df.columns)

print(f"Lokal sütunlar: {', '.join(sorted(local_cols))}")
print(f"Canlı sütunlar: {', '.join(sorted(live_cols))}")

missing_in_live = local_cols - live_cols

if missing_in_live:
    print(f"\n⚠️ Canlıda eksik sütunlar: {', '.join(sorted(missing_in_live))}")
    print("\nÖNEMLİ: PostgreSQL'de sütun eklemek için ALTER TABLE kullanılmalı.")
    print("Bu script verileri sync eder ancak şema değişikliği yapmaz.")
    print("Eksik sütunlar nedeniyle sync iptal ediliyor.\n")
    
    # Çözüm önerisi
    print("="*80)
    print("ÇÖL ZÜM ÖNERİSİ")
    print("="*80)
    print("\nSeçenek 1: Şemayı manuel güncelleyin (Supabase Dashboard)")
    print("Seçenek 2: Yeni tablo oluşturup verileri migrate edin")
    print("\nDetaylar için lütfen önce şema uyumluluğunu sağlayın.")
    
else:
    print("\n✅ Şema uyumlu, sync başlayabilir!")
    
    # 2. Veri sync
    print("\n2️⃣ VERİ SYNC")
    print("-"*80)
    
    # Tüm lokaldeki ürünleri al
    local_products = pd.read_sql("SELECT * FROM ayarlar_urunler ORDER BY urun_adi", local_engine)
    live_products = pd.read_sql("SELECT urun_adi FROM ayarlar_urunler", live_engine)
    
    live_product_names = set(live_products['urun_adi'].tolist())
    
    inserts = []
    updates = []
    
    for _, row in local_products.iterrows():
        if row['urun_adi'] in live_product_names:
            updates.append(row.to_dict())
        else:
            inserts.append(row.to_dict())
    
    print(f"Yeni ürünler: {len(inserts)}")
    print(f"Güncellenecek ürünler: {len(updates)}")
    
    confirm = input("\nDevam edilsin mi? (e/h): ")
    
    if confirm.lower() == 'e':
        with live_engine.begin() as conn:
            # INSERT
            if inserts:
                insert_df = pd.DataFrame(inserts)
                insert_df = insert_df.where(pd.notnull(insert_df), None)
                insert_df.to_sql('ayarlar_urunler', conn, if_exists='append', index=False)
                print(f"✅ {len(inserts)} yeni ürün eklendi")
            
            # UPDATE
            if updates:
                for update_row in updates:
                    set_cols = [c for c in local_products.columns if c != 'urun_adi']
                    set_clause = ", ".join([f"{col} = :{col}" for col in set_cols])
                    sql = f"UPDATE ayarlar_urunler SET {set_clause} WHERE urun_adi = :urun_adi"
                    params = {k: (None if pd.isna(v) else v) for k, v in update_row.items()}
                    conn.execute(text(sql), params)
                print(f"✅ {len(updates)} ürün güncellendi")
        
        print("\n✅ Sync tamamlandı!")
    else:
        print("\nSync iptal edildi.")
