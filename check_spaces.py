
import pandas as pd
from sqlalchemy import create_engine, text

db_url = 'sqlite:///ekleristan_local.db'
engine = create_engine(db_url)

with open('spaces.txt', 'w', encoding='utf-8') as f:
    f.write("--- DEPARTMANLAR (Isim Analizi) ---\n")
    with engine.connect() as conn:
        df_dept = pd.read_sql("SELECT bolum_adi FROM ayarlar_bolumler WHERE aktif = 1", conn)
        for name in df_dept['bolum_adi']:
            f.write(f"'{name}' Len: {len(name)}\n")

    f.write("\n--- URUNLER (Departman Analizi) ---\n")
    with engine.connect() as conn:
        df_urun = pd.read_sql("SELECT DISTINCT sorumlu_departman FROM ayarlar_urunler", conn)
        df_urun = df_urun.dropna() # handle NaNs
        for name in df_urun['sorumlu_departman']:
             # check if not None
            if name is not None:
                s_name = str(name)
                f.write(f"'{s_name}' Len: {len(s_name)}\n")
