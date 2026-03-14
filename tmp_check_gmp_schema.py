import pandas as pd
from database.connection import get_engine

try:
    engine = get_engine()
    df = pd.read_sql("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'gmp_soru_havuzu'", engine)
    print("gmp_soru_havuzu columns:")
    print(df)
    
    df2 = pd.read_sql("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'gmp_denetim_kayitlari'", engine)
    print("\ngmp_denetim_kayitlari columns:")
    print(df2)
except Exception as e:
    print("Error:", e)
