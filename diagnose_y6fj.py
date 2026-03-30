import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

# Teşhis Dosyası Oluşturma betiği
def diagnose(ref_code):
    try:
        engine = create_engine("sqlite:///c:/Projeler/S_program/EKLERİSTAN_QMS/ekleristan_local.db")
        with engine.connect() as conn:
            q = text("SELECT hata_mesaji, stack_trace, modul FROM hata_loglari WHERE hata_kodu LIKE :c")
            res = conn.execute(q, {"c": f"%{ref_code}%"}).fetchone()
            
            with open("C:/Projeler/S_program/EKLERİSTAN_QMS/y6fj_debug.txt", "w", encoding="utf-8") as f:
                if res:
                    f.write(f"HATA MESAJI: {res[0]}\n")
                    f.write(f"MODUL: {res[2]}\n")
                    f.write("-" * 50 + "\n")
                    f.write(f"STACK TRACE:\n{res[1]}\n")
                else:
                    f.write("Hata referansı DB'de bulunamadı.")
    except Exception as e:
        with open("C:/Projeler/S_program/EKLERİSTAN_QMS/y6fj_debug.txt", "w", encoding="utf-8") as f:
            f.write(f"TEŞHİS SCRIPTI HATASI: {e}")

if __name__ == "__main__":
    diagnose("Y6FJ")
