import sys
import os
from sqlalchemy import text
import io

sys.path.append(os.getcwd())
from database.connection import get_engine

def dump_to_file():
    engine = get_engine()
    output = []
    output.append(f"Engine URL: {engine.url}")
    
    with engine.connect() as conn:
        output.append("\n--- MODULLER (ayarlar_moduller) ---")
        try:
            res = conn.execute(text("SELECT modul_anahtari, modul_etiketi FROM ayarlar_moduller")).fetchall()
            for r in res:
                output.append(f"Anahtar: [{r[0]}] | Etiket: [{r[1]}]")
        except Exception as e:
            output.append(f"Hata: {e}")

        output.append("\n--- TEST YETKILERI (rol_adi='TEST_ROLU') ---")
        try:
            res = conn.execute(text("SELECT modul_adi, erisim_turu, sadece_kendi_bolumu FROM ayarlar_yetkiler WHERE rol_adi = 'TEST_ROLU'")).fetchall()
            for r in res:
                output.append(f"Modul(adi): [{r[0]}] | Yetki: [{r[1]}] | KendiBolum: [{r[2]}]")
        except Exception as e:
            output.append(f"Hata: {e}")

    with open("db_content_dump.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(output))
    print("Dump completed to db_content_dump.txt")

if __name__ == "__main__":
    dump_to_file()
