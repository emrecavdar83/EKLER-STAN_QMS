import pandas as pd
from database.connection import get_engine

try:
    engine = get_engine()
    df = pd.read_sql("SELECT id, ad_soyad, kullanici_adi, rol, bolum, gorev, durum FROM personel WHERE ad_soyad LIKE '%GÜLAY GEM%' OR ad_soyad LIKE '%GULAY GEM%'", engine)
    print("Found user(s):")
    print(df.to_dict(orient='records'))
except Exception as e:
    print(e)
