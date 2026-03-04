import sys
from sqlalchemy import text
from database.connection import get_engine
from datetime import datetime
from logic.db_writer import guvenli_kayit_ekle
from soguk_oda_utils import kaydet_olcum

engine = get_engine()

print("--- TEST 1: KPI INSERT ---")
try:
    simdi = datetime.now()
    veri_paketi = [
        str(simdi.date()), simdi.strftime("%H:%M"), "GÜNDÜZ VARDİYASI", "Test Ürün",
        "", "LOT123", str(simdi.date()), "1",
        0.0, 0.0, 0.0, "ONAY", "Test_User", str(simdi),
        "", "", "Uygun", "Uygun", "Test Not", "test.jpg", "data:image/jpeg;base64,12345"
    ]
    res1 = guvenli_kayit_ekle("Urun_KPI_Kontrol", veri_paketi)
    print("KPI Insert Result:", res1)
except Exception as e:
    print("KPI Exception:", e)

print("\n--- TEST 2: SOĞUK ODA INSERT ---")
try:
    with engine.begin() as conn:
        oda = conn.execute(text("SELECT id FROM soguk_odalar LIMIT 1")).fetchone()
        oda_id = oda[0] if oda else 1
    
    res2 = kaydet_olcum(engine, oda_id, 4.5, "Test_User", None, 1, 0)
    print("Soguk Oda Insert Result:", res2)
except Exception as e:
    print("Soguk Oda Exception:", e)
