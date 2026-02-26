import sys
import os

# Proje kök dizinini başa ekle
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from database.connection import get_engine
from sqlalchemy import text

def run_pg_migration():
    engine = get_engine()
    # Emniyet kontrolü: Sadece PostgreSQL/Postgresql+psycopg2 ise çalıştır
    if 'postgresql' not in str(engine.url).lower():
        print("HATA: Bu script sadece PostgreSQL (Bulut) ortamı içindir!")
        return

    print(f"🚀 PostgreSQL Migration Başlatılıyor: {engine.url.host}")

    with engine.begin() as conn:
        # --- MIGRATION 001 & 002 (Constraints & Table Structures) ---
        print("1. Tablo kısıtlamaları ve yapılar güncelleniyor...")
        
        # ayarlar_urunler UNIQUE constraint
        conn.execute(text("ALTER TABLE ayarlar_urunler ADD CONSTRAINT unq_urun_adi UNIQUE (urun_adi)"))
        
        # urun_parametreleri UNIQUE constraint
        conn.execute(text("ALTER TABLE urun_parametreleri ADD CONSTRAINT unq_urun_param UNIQUE (urun_adi, parametre_adi)"))
        
        # tanim_metotlar UNIQUE constraint
        conn.execute(text("ALTER TABLE tanim_metotlar ADD CONSTRAINT unq_metot_adi UNIQUE (metot_adi)"))
        
        # kimyasal_envanter UNIQUE constraint
        conn.execute(text("ALTER TABLE kimyasal_envanter ADD CONSTRAINT unq_kimyasal_adi UNIQUE (kimyasal_adi)"))

        # --- MIGRATION 003 (Temizlik Validasyon Tabloları) ---
        print("2. Temizlik validasyon tabloları oluşturuluyor...")
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS temizlik_dogrulama_kriterleri (
                id SERIAL PRIMARY KEY,
                metot_id BIGINT,
                yuzey_tipi VARCHAR(255),
                min_konsantrasyon DECIMAL,
                max_konsantrasyon DECIMAL,
                min_sicaklik DECIMAL,
                max_sicaklik DECIMAL,
                temas_suresi_dk INTEGER,
                rlu_esik_degeri DECIMAL,
                notlar TEXT,
                aktif INTEGER DEFAULT 1,
                FOREIGN KEY (metot_id) REFERENCES tanim_metotlar(id)
            )
        """))
        
        # Index ekle
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS idx_val_metot_yuzey ON temizlik_dogrulama_kriterleri (metot_id, yuzey_tipi)"))

        # tanim_metotlar tablosuna sütun ekle
        try:
            conn.execute(text("ALTER TABLE tanim_metotlar ADD COLUMN uygulama_notu TEXT"))
        except: pass

        # --- MIGRATION 004 (Master Plan FKs) ---
        print("3. Ayarlar Temizlik Plani güncelleniyor...")
        try:
            conn.execute(text("ALTER TABLE ayarlar_temizlik_plani ADD COLUMN metot_id BIGINT"))
            conn.execute(text("ALTER TABLE ayarlar_temizlik_plani ADD COLUMN yuzey_tipi VARCHAR(255)"))
        except: pass

    print("✅ PostgreSQL Migration başarıyla tamamlandı.")

if __name__ == "__main__":
    run_pg_migration()
