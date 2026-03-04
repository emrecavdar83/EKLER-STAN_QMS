import sys
sys.path.insert(0, r'c:\Projeler\S_program\EKLERİSTAN_QMS')
from database.connection import get_engine
from sqlalchemy import text

engine = get_engine()
today = '2026-03-01'

print(f"DB: {engine.url}")
print(f"Tarih: {today}")
print("=" * 40)

with engine.connect() as conn:
    kpi = conn.execute(text(f"SELECT COUNT(*) FROM urun_kpi_kontrol WHERE tarih='{today}'")).scalar()
    print(f"KPI kayit        : {kpi}")

    uretim = conn.execute(text(f"SELECT COUNT(*) FROM depo_giris_kayitlari WHERE tarih='{today}'")).scalar()
    print(f"Uretim kayit     : {uretim}")

    try:
        sosts = conn.execute(text(f"SELECT COUNT(*) FROM sicaklik_olcumleri WHERE DATE(olcum_zamani)='{today}'")).scalar()
        print(f"SOSTS sicaklik   : {sosts}")
    except Exception as e:
        print(f"SOSTS: HATA - {e}")

    try:
        hijyen = conn.execute(text(f"SELECT COUNT(*) FROM hijyen_kontrol_kayitlari WHERE tarih='{today}'")).scalar()
        print(f"Hijyen kayit     : {hijyen}")
    except Exception as e:
        print(f"Hijyen: HATA - {e}")

    print("\n--- SON KAYIT TARIHLERİ ---")
    try:
        son_kpi = conn.execute(text("SELECT MAX(tarih) FROM urun_kpi_kontrol")).scalar()
        print(f"KPI son kayit    : {son_kpi}")
    except: pass
    try:
        son_ur = conn.execute(text("SELECT MAX(tarih) FROM depo_giris_kayitlari")).scalar()
        print(f"Uretim son kayit : {son_ur}")
    except: pass
    try:
        son_so = conn.execute(text("SELECT MAX(olcum_zamani) FROM sicaklik_olcumleri")).scalar()
        print(f"SOSTS son olcum  : {son_so}")
    except: pass
