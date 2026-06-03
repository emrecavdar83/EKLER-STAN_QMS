import sys
sys.path.append('.')
from logic.data_fetcher import run_query

try:
    df = run_query("SELECT calisan_adi_soyadi FROM ik_personel_karti WHERE durum='AKTİF'")
    print("ik_personel_karti records:", len(df))
except Exception as e:
    print("ik_personel_karti ERROR:", e)

try:
    df = run_query("SELECT * FROM tum_personel")
    print("tum_personel records:", len(df))
except Exception as e:
    print("tum_personel ERROR:", e)
