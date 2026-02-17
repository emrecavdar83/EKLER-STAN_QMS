# -*- coding: utf-8 -*-
"""
Üretim Kayıtları Tablosu - 'saat' Kolonu Migrasyonu
Hem LOKAL hem de CANLI veritabanına uygulanır.
"""
import os
from sqlalchemy import create_engine, text
import toml

def run_migration(engine, db_name):
    print(f"\n🚀 {db_name} Migrasyonu Başlatılıyor...")
    try:
        with engine.connect() as conn:
            # Kolon var mı kontrol et
            if 'sqlite' in str(engine.url):
                res = conn.execute(text("PRAGMA table_info(depo_giris_kayitlari)"))
                columns = [row[1] for row in res.fetchall()]
            else:
                res = conn.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'depo_giris_kayitlari'
                """))
                columns = [row[0] for row in res.fetchall()]

            if 'saat' not in columns:
                print(f"➕ 'saat' kolonu ekleniyor...")
                conn.execute(text("ALTER TABLE depo_giris_kayitlari ADD COLUMN saat TEXT"))
                conn.commit()
                print(f"✅ 'saat' kolonu başarıyla eklendi.")
            else:
                print(f"ℹ️ 'saat' kolonu zaten mevcut.")
    except Exception as e:
        print(f"❌ {db_name} Hatası: {e}")

if __name__ == "__main__":
    # 1. Lokal SQLite
    local_url = 'sqlite:///ekleristan_local.db'
    local_engine = create_engine(local_url)
    run_migration(local_engine, "LOKAL")

    # 2. Canlı PostgreSQL
    try:
        secrets = toml.load('.streamlit/secrets.toml')
        live_url = secrets.get('DB_URL') or secrets.get('streamlit', {}).get('DB_URL')
        if live_url:
            live_url = live_url.strip('"')
            live_engine = create_engine(live_url)
            run_migration(live_engine, "CANLI")
        else:
            print("\n⚠️ CANLI veritabanı URL'si bulunamadı (secrets.toml).")
    except Exception as e:
        print(f"\n⚠️ CANLI migrasyonu yapılamadı: {e}")

    print("\n✨ Migrasyon işlemi tamamlandı.")
