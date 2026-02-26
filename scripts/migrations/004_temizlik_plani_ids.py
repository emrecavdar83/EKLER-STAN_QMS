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
        print("1. ayarlar_temizlik_plani tablosuna yeni sütunlar ekleniyor...")
        
        # metot_id ekle
        try:
            conn.execute(text("ALTER TABLE ayarlar_temizlik_plani ADD COLUMN metot_id INTEGER"))
            print("metot_id sütunu eklendi.")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("metot_id sütunu zaten mevcut.")
            else:
                print(f"Uyarı (metot_id): {e}")

        # yuzey_tipi ekle
        try:
            conn.execute(text("ALTER TABLE ayarlar_temizlik_plani ADD COLUMN yuzey_tipi TEXT"))
            print("yuzey_tipi sütunu eklendi.")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("yuzey_tipi sütunu zaten mevcut.")
            else:
                print(f"Uyarı (yuzey_tipi): {e}")

    print("✅ Migration 004 tamamlandı.")

if __name__ == "__main__":
    run()
