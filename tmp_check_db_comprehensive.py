import sys
import os
from sqlalchemy import text, create_engine
import sqlite3

def check_everything():
    print("=== DB HEDEF ANALIZI ===")
    
    # 1. SQLite Kontrolü
    print("\n[A] SQLite (ekleristan_local.db) Kontrolü:")
    if os.path.exists('ekleristan_local.db'):
        conn = sqlite3.connect('ekleristan_local.db')
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ayarlar_moduller'")
        res = cur.fetchone()
        print(f"ayarlar_moduller tablosu SQLite'da var mı? : {'EVET' if res else 'HAYIR'}")
        if res:
             cur.execute("SELECT COUNT(*) FROM ayarlar_moduller")
             print(f"Modul Sayısı: {cur.fetchone()[0]}")
        conn.close()
    else:
        print("ekleristan_local.db dosyası bulunamadı.")

    # 2. engine (connection.py) Hedef Kontrolü
    sys.path.append(os.getcwd())
    try:
        from database.connection import get_engine
        engine = get_engine()
        print(f"\n[B] get_engine() Hedefi: {engine.url}")
        
        with engine.connect() as conn:
            # Dialect kontrolü
            if engine.dialect.name == 'postgresql':
                print("Hedef: PostgreSQL (Bulut)")
                res = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ayarlar_moduller')")).fetchone()
                print(f"ayarlar_moduller tablosu PostgreSQL'de var mı? : {'EVET' if res[0] else 'HAYIR'}")
            else:
                print("Hedef: SQLite (Yerel)")
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    check_everything()
