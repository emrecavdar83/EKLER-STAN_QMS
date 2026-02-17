"""
Ultra Güvenli Manuel Sync
===========================
Bu script sadece kritik 2 tabloyu sync eder:
1. ayarlar_yetkiler
2. personel

Özellikler:
- Tablolardan bağımsız sync
- Hata durumunda otomatik rollback
- Detaylı log
- Mevcut veriyi koruma (UPSERT)
"""

import pandas as pd
from sqlalchemy import create_engine, text
import toml
import sys

# Engines
local_engine = create_engine('sqlite:///ekleristan_local.db')
secrets = toml.load('.streamlit/secrets.toml')
live_url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
live_engine = create_engine(live_url, pool_pre_ping=True)

def safe_sync_table(table_name, pk_cols):
    """
    Güvenli tablo sync - sadece yeni kayıtları ekler veya var olanları günceller.
    Silme işlemi YAPMAZ.
    """
    print(f"\n{'='*60}")
    print(f"Syncing: {table_name}")
    print('='*60)
    
    try:
        # Lokal veriyi al
        local_df = pd.read_sql(f"SELECT * FROM {table_name}", local_engine)
        print(f"Lokal kayıt sayısı: {len(local_df)}")
        
        # Canlı veriyi al
        live_df = pd.read_sql(f"SELECT * FROM {table_name}", live_engine)
        print(f"Canlı kayıt sayısı: {len(live_df)}")
        
        if local_df.empty:
            print("⚠️ Lokal tablo boş, sync atlanıyor.")
            return {"status": "skipped", "reason": "empty_local"}
        
        # PK bazlı karşılaştırma
        if isinstance(pk_cols, str):
            pk_cols = [pk_cols]
        
        # Canlıda olan kayıtları set'e al
        live_keys = set()
        if not live_df.empty:
            for _, row in live_df.iterrows():
                key = tuple(row[col] for col in pk_cols)
                live_keys.add(key)
        
        inserts = []
        updates = []
        
        for _, row in local_df.iterrows():
            key = tuple(row[col] for col in pk_cols)
            
            if key in live_keys:
                # Güncelleme gerekebilir
                updates.append(row.to_dict())
            else:
                # Yeni kayıt
                inserts.append(row.to_dict())
        
        print(f"\nYeni kayıtlar: {len(inserts)}")
        print(f"Güncellenecekler: {len(updates)}")
        
        # Transaction ile uygula
        with live_engine.begin() as conn:
            # INSERT
            if inserts:
                insert_df = pd.DataFrame(inserts)
                # NaN değerleri None yap
                insert_df = insert_df.where(pd.notnull(insert_df), None)
                insert_df.to_sql(table_name, conn, if_exists='append', index=False)
                print(f"✅ {len(inserts)} yeni kayıt eklendi")
            
            # UPDATE
            if updates:
                for update_row in updates:
                    # WHERE clause
                    where_parts = [f"{col} = :{col}" for col in pk_cols]
                    where_clause = " AND ".join(where_parts)
                    
                    # SET clause (PK hariç tüm kolonlar)
                    set_cols = [c for c in local_df.columns if c not in pk_cols]
                    set_parts = [f"{col} = :{col}" for col in set_cols]
                    set_clause = ", ".join(set_parts)
                    
                    sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
                    
                    # NaN'ları None yap
                    params = {k: (None if pd.isna(v) else v) for k, v in update_row.items()}
                    
                    conn.execute(text(sql), params)
                
                print(f"✅ {len(updates)} kayıt güncellendi")
        
        return {
            "status": "success",
            "inserted": len(inserts),
            "updated": len(updates)
        }
        
    except Exception as e:
        print(f"❌ HATA: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print("="*60)
    print("GÜVENLİ SYNC BAŞLIYOR")
    print("="*60)
    print("\n⚠️ Bu işlem:")
    print("  - Sadece yeni kayıtları EKLER")
    print("  - Mevcut kayıtları GÜNCELLER")
    print("  - HİÇBİR KAYIT SİLMEZ")
    print("  - Hata durumunda otomatik ROLLBACK yapar")
    
    input("\nDevam etmek için ENTER'a basın (İptal: Ctrl+C)...")
    
    # 1. Yetkiler Tablosu
    result1 = safe_sync_table("ayarlar_yetkiler", ["rol_adi", "modul_adi"])
    
    # 2. Personel Tablosu (ID bazlı)
    result2 = safe_sync_table("personel", "id")
    
    print("\n" + "="*60)
    print("SYNC TAMAMLANDI")
    print("="*60)
    print(f"\nayarlar_yetkiler: {result1}")
    print(f"personel: {result2}")
    
    if result1.get("status") == "success" and result2.get("status") == "success":
        print("\n✅ TÜM İŞLEMLER BAŞARILI!")
    else:
        print("\n⚠️ Bazı tablolarda sorun oluştu, detayları kontrol edin.")
