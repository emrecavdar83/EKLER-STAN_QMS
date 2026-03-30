import sqlite3
import os

db_path = 'c:/Projeler/S_program/EKLERİSTAN_QMS/ekleristan_local.db'
if not os.path.exists(db_path):
    print("Database not found")
else:
    try:
        conn = sqlite3.connect(db_path)
        # 960L hatasını bul
        res = conn.execute("SELECT hata_kodu, hata_mesaji, stack_trace, zaman_damgasi FROM hata_loglari WHERE hata_kodu LIKE '%960L%' ORDER BY id DESC LIMIT 1").fetchone()
        if res:
            with open('error_debug_960l.txt', 'w', encoding='utf-8') as f:
                f.write(f"KOD: {res[0]}\n")
                f.write(f"MESAJ: {res[1]}\n")
                # Zaman damgası kolon sırası (res[3])
                f.write(f"TRACE:\n{res[2]}")
            print("Error details written to error_debug_960l.txt")
        else:
            print("Error 960L not found in logs")
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")
