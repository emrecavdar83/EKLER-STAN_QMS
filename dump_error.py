from sqlalchemy import create_engine, text
import os

engine = create_engine("sqlite:///c:/Projeler/S_program/EKLERİSTAN_QMS/ekleristan_local.db")
output_file = "c:/Projeler/S_program/EKLERİSTAN_QMS/error_dump_mlqy.txt"

try:
    with engine.connect() as conn:
        res = conn.execute(text("SELECT hata_mesaji, stack_trace, modul FROM hata_loglari WHERE hata_kodu LIKE '%MLQY%' OR id = (SELECT MAX(id) FROM hata_loglari)")).fetchone()
        
        if res:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"HATA MESAJI: {res[0]}\n")
                f.write(f"MODUL: {res[2]}\n")
                f.write("-" * 50 + "\n")
                f.write(f"STACK TRACE:\n{res[1]}\n")
            print(f"BİLGİ: Hata detayları {output_file} dosyasına yazıldı.")
        else:
            print("Hata bulunamadı.")
except Exception as e:
    print(f"SORGULAMA HATASI: {e}")
