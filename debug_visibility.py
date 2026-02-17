
import pandas as pd
from sqlalchemy import create_engine, text

db_url = 'sqlite:///ekleristan_local.db'
engine = create_engine(db_url)

with open('debug_output.txt', 'w', encoding='utf-8') as f:
    f.write("--- DEPARTMANLAR (ayarlar_bolumler) ---\n")
    with engine.connect() as conn:
        df_dept = pd.read_sql("SELECT * FROM ayarlar_bolumler WHERE aktif = 1", conn)
        f.write(df_dept[['id', 'bolum_adi', 'ana_departman_id']].to_string() + "\n")

    f.write("\n--- ÜRÜNLER (ayarlar_urunler) SAMPLE ---\n")
    with engine.connect() as conn:
        df_urun = pd.read_sql("SELECT urun_adi, sorumlu_departman FROM ayarlar_urunler LIMIT 20", conn)
        f.write(df_urun.to_string() + "\n")

    f.write("\n--- PERSONEL (Sample) ---\n")
    with engine.connect() as conn:
        # Check all roles to find the user
        df_per = pd.read_sql("SELECT id, ad_soyad, kullanici_adi, rol, departman_id FROM personel WHERE rol LIKE '%Sorumlu%' OR rol LIKE '%AMİRİ%' LIMIT 20", conn)
        
        # Do a manual mapping to check what app.py logic sees
        dept_map = df_dept.set_index('id')['bolum_adi'].to_dict()
        df_per['bolum_adi'] = df_per['departman_id'].map(dept_map)
        
        f.write(df_per.to_string() + "\n")
