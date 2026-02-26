import sys
import os

# Proje kök dizinini başa ekle
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from database.connection import get_engine
from sqlalchemy import text

def run():
    engine = get_engine()
    print(f"Bağlanılan veritabanı: {engine.url}")
    
    with engine.begin() as conn:
        print("1. temizlik_dogrulama_kriterleri tablosu oluşturuluyor...")
        # Yeni tablo
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS temizlik_dogrulama_kriterleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metot_id INTEGER,
                yuzey_tipi TEXT,
                min_konsantrasyon REAL,
                max_konsantrasyon REAL,
                min_sicaklik REAL,
                max_sicaklik REAL,
                temas_suresi_dk INTEGER,
                rlu_esik_degeri REAL,
                notlar TEXT,
                aktif INTEGER DEFAULT 1,
                FOREIGN KEY (metot_id)
                    REFERENCES tanim_metotlar(id)
            )
        """))

        print("2. tanim_metotlar tablosuna uygulama_notu sütunu ekleniyor...")
        # tanim_metotlar tablosuna eksik sütunlar ekle
        # (SQLite ALTER TABLE sadece sütun ekler)
        try:
            conn.execute(text(
                "ALTER TABLE tanim_metotlar ADD COLUMN uygulama_notu TEXT"
            ))
            print("Sütun başarıyla eklendi.")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("Sütun zaten mevcut, atlanıyor.")
            else:
                print(f"Uyarı: Sütun eklenirken bir hata oluştu: {e}")

    print("✅ Migration 003 tamamlandı.")

if __name__ == "__main__":
    run()
