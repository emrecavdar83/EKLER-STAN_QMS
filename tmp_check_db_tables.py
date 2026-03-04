import sys
import os
from sqlalchemy import text

# Proje kök dizinini yola ekle
sys.path.append(os.getcwd())

from database.connection import get_engine

def check_db():
    engine = get_engine()
    print(f"Engine URL: {engine.url}")
    
    with engine.connect() as conn:
        print("\n[A] SQLite Tablo Listesi:")
        try:
            res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            for r in res:
                print(f"- {r[0]}")
        except Exception as e:
            print(f"SQLite master okuma hatası: {e}")

        print("\n[B] 'ayarlar_moduller' İçeriği:")
        try:
            res = conn.execute(text("SELECT * FROM ayarlar_moduller")).fetchall()
            for r in res:
                print(r)
        except Exception as e:
            print(f"ayarlar_moduller okuma hatası: {e}")

if __name__ == "__main__":
    check_db()
