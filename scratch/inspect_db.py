import os
import sys
from sqlalchemy import create_engine, text
import pandas as pd

# Set encoding for Windows console
if sys.platform == 'win32':
    import _locale
    _locale._getdefaultlocale = (lambda *args: ['en_US', 'utf8'])

def get_engine():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return create_engine(db_url)
    return create_engine('sqlite:///ekleristan_local.db')

def inspect():
    engine = get_engine()
    with engine.connect() as conn:
        print("\n--- PERSONEL KAYITLARI (Emre Cavdar & Admin) ---")
        try:
            res = conn.execute(text("SELECT id, ad_soyad, kullanici_adi, rol, departman_id, durum FROM personel WHERE ad_soyad LIKE '%Emre%' OR kullanici_adi = 'Admin'"))
            items = [dict(r._mapping) for r in res.fetchall()]
            for item in items:
                print(item)
        except Exception as e:
            print(f"Hata (Personel): {e}")

        print("\n--- DEPARTMANLAR (İlk 20) ---")
        try:
            res = conn.execute(text("SELECT id, ad, kod, ust_id FROM qms_departmanlar LIMIT 20"))
            items = [dict(r._mapping) for r in res.fetchall()]
            for item in items:
                print(item)
        except Exception as e:
            print(f"Hata (Departmanlar): {e}")

        print("\n--- SISTEM PARAMETRELERI ---")
        try:
            res = conn.execute(text("SELECT anahtar, deger FROM sistem_parametreleri"))
            items = [dict(r._mapping) for r in res.fetchall()]
            for item in items:
                print(f"{item['anahtar']}: {item['deger'][:100]}...")
        except Exception as e:
            print(f"Hata (Parametreler): {e}")

if __name__ == "__main__":
    inspect()
