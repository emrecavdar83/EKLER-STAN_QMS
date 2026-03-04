import sys
import os
from sqlalchemy import text

# Force UTF-8 for printing
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append(os.getcwd())
from database.connection import get_engine

def dump_db():
    engine = get_engine()
    print(f"Engine URL: {engine.url}")
    
    with engine.connect() as conn:
        print("\n--- MODULLER (ayarlar_moduller) ---")
        try:
            res = conn.execute(text("SELECT modul_anahtari, modul_etiketi FROM ayarlar_moduller")).fetchall()
            for r in res:
                print(f"Anahtar: [{r[0]}] | Etiket: [{r[1]}]")
        except Exception as e:
            print(f"Hata: {e}")

        print("\n--- TEST YETKILERI (rol_adi='TEST_ROLU') ---")
        try:
            res = conn.execute(text("SELECT modul_adi, erisim_turu, sadece_kendi_bolumu FROM ayarlar_yetkiler WHERE rol_adi = 'TEST_ROLU'")).fetchall()
            for r in res:
                print(f"Modul(adi): [{r[0]}] | Yetki: [{r[1]}] | KendiBolum: [{r[2]}]")
        except Exception as e:
            print(f"Hata: {e}")

if __name__ == "__main__":
    dump_db()
