
from sqlalchemy import create_engine, text
import toml
import os

def run_migration():
    print("--- SOSTS Schema Migration (UNIQUE Constraint) ---")
    
    try:
        secrets = toml.load('.streamlit/secrets.toml')
        live_url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
        live_engine = create_engine(live_url)
    except Exception as e:
        print(f"HATA: Canlı veritabanı bağlantısı kurulamadı: {e}")
        return

    # PostgreSQL / SQLite uyumlu UNIQUE Index (Aynı zamanda kısıtlama işlevi görür)
    # Önce varsa temizleyelim (hata almamak için) veya doğrudan CREATE UNIQUE INDEX
    migration_sql = text("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_olcum_plani_oda_zaman 
        ON olcum_plani (oda_id, beklenen_zaman);
    """)

    print(f"İşleniyor: CANLI (PostgreSQL/Supabase)")
    try:
        with live_engine.begin() as conn:
            # 1. Önce mükerrer kayıtları temizle (Eğer index oluşturulamazsa sebebi budur)
            print("  - Mükerrer kayıtlar kontrol ediliyor/temizleniyor...")
            # PostgreSQL için mükerrer temizleme (en yüksek ID'yi tut)
            conn.execute(text("""
                DELETE FROM olcum_plani 
                WHERE id NOT IN (
                    SELECT MAX(id) 
                    FROM olcum_plani 
                    GROUP BY oda_id, beklenen_zaman
                );
            """))
            
            # 2. UNIQUE INDEX oluştur
            print("  - UNIQUE Index oluşturuluyor...")
            conn.execute(migration_sql)
            
        print("OK: Migration başarıyla tamamlandı.")
    except Exception as e:
        print(f"HATA: Migration sırasında sorun oluştu: {e}")

if __name__ == "__main__":
    run_migration()
