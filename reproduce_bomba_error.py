import pandas as pd
from sqlalchemy import create_engine, text
import toml
from datetime import datetime

# Mimic app.py connection
try:
    secrets = toml.load('.streamlit/secrets.toml')
    url = secrets.get('DB_URL') or secrets['streamlit']['DB_URL']
    url = url.strip('"')
    print(f"Connecting to: {url}")
    engine = create_engine(url)
except Exception as e:
    print(f"Connection setup failed: {e}")
    # Fallback to local sqlite if secrets fail
    engine = create_engine('sqlite:///ekleristan_local.db')

def reproduce_error():
    print("Attempting to insert KPI record...")
    
    # Simulate veri_paketi from app.py
    # [date, time, vardiya, urun, "", lot_no, stt, numune, avg1, avg2, avg3, karar, user, timestamp, "", "", tat, goruntu, notlak, foto]
    simdi = datetime.now()
    veri = [
        str(simdi.date()),              # 0
        simdi.strftime("%H:%M"),        # 1
        "GÜNDÜZ VARDİYASI",             # 2
        "BOMBA ÜRÜN",                   # 3 (Product Name)
        "",                             # 4
        "LOT123",                       # 5
        str(simdi.date()),              # 6
        "1",                            # 7
        10.5, 0.0, 0.0,                 # 8, 9, 10
        "ONAY",                         # 11
        "TEST_USER",                    # 12
        str(simdi),                     # 13
        "", "",                         # 14, 15
        "Uygun",                        # 16
        "Uygun",                        # 17
        "Test Notu",                    # 18
        "test_foto.jpg"                 # 19
    ]
    
    try:
        with engine.connect() as conn:
            sql = """INSERT INTO urun_kpi_kontrol (tarih, saat, vardiya, urun, lot_no, stt, numune_no, olcum1, olcum2, olcum3, karar, kullanici, tat, goruntu, notlar, fotograf_yolu)
                     VALUES (:t, :sa, :v, :u, :l, :stt, :num, :o1, :o2, :o3, :karar, :kul, :tat, :gor, :notlar, :foto)"""
            params = {
                "t": veri[0], "sa": veri[1], "v": veri[2], "u": veri[3],
                "l": veri[5], "stt": veri[6], "num": veri[7],
                "o1": veri[8], "o2": veri[9], "o3": veri[10],
                "karar": veri[11], "kul": veri[12],
                "tat": veri[16], "gor": veri[17], "notlar": veri[18],
                "foto": veri[19] if len(veri) > 19 else None
            }
            conn.execute(text(sql), params)
            conn.commit()
            print("✅ Insert successful!")
    except Exception as e:
        print(f"❌ Insert failed: {e}")

if __name__ == "__main__":
    reproduce_error()
