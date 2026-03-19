
from sqlalchemy import create_engine, text
import toml
import pandas as pd
from datetime import datetime, timedelta
import pytz

_TZ_IST = pytz.timezone('Europe/Istanbul')
def _now():
    return datetime.now(_TZ_IST).replace(tzinfo=None, microsecond=0)

def test_plan_gen():
    secrets = toml.load(".streamlit/secrets.toml")
    db_url = secrets.get("DB_URL") or secrets.get("streamlit", {}).get("DB_URL")
    engine = create_engine(db_url)
    
    # 1. Create a dummy room
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM olcum_plani WHERE oda_id = 999"))
        conn.execute(text("DELETE FROM soguk_oda_planlama_kurallari WHERE oda_id = 999"))
        conn.execute(text("DELETE FROM soguk_odalar WHERE id = 999"))
        conn.execute(text("INSERT INTO soguk_odalar (id, oda_kodu, oda_adi, aktif, qr_token) VALUES (999, 'TEST-RULES', 'Rule Test Room', 1, 'TEST-TOKEN-999')"))
        
        # 2. Add cross-day rule: 23-07 with 4h frequency
        conn.execute(text("""
            INSERT INTO soguk_oda_planlama_kurallari (oda_id, kural_adi, baslangic_saati, bitis_saati, siklik)
            VALUES (999, 'Gece', 23, 7, 4)
        """))
    
    # 3. Generate plan
    import soguk_oda_utils
    soguk_oda_utils.plan_uret(engine, gun_sayisi=1)
    
    # 4. Check results
    with engine.connect() as conn:
        res = conn.execute(text("SELECT beklenen_zaman FROM olcum_plani WHERE oda_id = 999 ORDER BY beklenen_zaman ASC")).fetchall()
        print("Generated slots for 23:00-07:00 (4h):")
        for r in res:
            print(r[0])
            
    # Cleanup
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM olcum_plani WHERE oda_id = 999"))
        conn.execute(text("DELETE FROM soguk_oda_planlama_kurallari WHERE oda_id = 999"))
        conn.execute(text("DELETE FROM soguk_odalar WHERE id = 999"))

if __name__ == "__main__":
    test_plan_gen()
