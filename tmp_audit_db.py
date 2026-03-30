from sqlalchemy import create_engine, text
import pandas as pd

# local db engine
engine = create_engine("sqlite:///c:/Projeler/S_program/EKLERİSTAN_QMS/ekleristan_local.db")

print("--- MODÜLLER ---")
try:
    with engine.connect() as conn:
        df_mod = pd.read_sql(text("SELECT id, modul_adi, modul_etiketi, modul_anahtari, aktif FROM ayarlar_moduller"), conn)
        print(df_mod.to_string())
except Exception as e:
    print(f"Modul Hatası: {e}")

print("\n--- SON 5 HATA LOGU ---")
try:
    with engine.connect() as conn:
        df_err = pd.read_sql(text("SELECT * FROM hata_loglari ORDER BY id DESC LIMIT 5"), conn)
        print(df_err.to_string())
except Exception as e:
    print(f"Hata Logu Hatası: {e}")

print("\n--- SON 5 SİSTEM LOGU ---")
try:
    with engine.connect() as conn:
        df_sys = pd.read_sql(text("SELECT * FROM sistem_loglari ORDER BY id DESC LIMIT 5"), conn)
        print(df_sys.to_string())
except Exception as e:
    print(f"Sistem Logu Hatası: {e}")
