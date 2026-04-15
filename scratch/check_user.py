from database.connection import get_engine
import pandas as pd
from sqlalchemy import text

engine = get_engine()
with engine.connect() as conn:
    res = conn.execute(text("SELECT ad_soyad, kullanici_adi, rol, durum FROM personel WHERE ad_soyad LIKE '%Emre%' OR kullanici_adi LIKE '%Emre%';"))
    df = pd.DataFrame(res.fetchall(), columns=res.keys())
    print(df.to_string())
