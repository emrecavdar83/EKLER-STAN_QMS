import sys
import os
import toml
import pandas as pd
from sqlalchemy import text

sys.path.append('c:\\Projeler\\S_program\\EKLERİSTAN_QMS')
os.environ['STREAMLIT_SECRETS'] = 'c:\\Projeler\\S_program\\EKLERİSTAN_QMS\\.streamlit\\secrets.toml'

from database.connection import get_engine

engine = get_engine()
with engine.connect() as conn:
    df = pd.read_sql(text("SELECT id, oda_adi, oda_kodu, qr_token, aktif FROM soguk_odalar"), conn)
    print("--- TUM ODALAR VE DURUMLARI ---")
    print(df.to_string())

    # Ozellikle EKMEK odasina bak
    ekmek = df[df['oda_adi'].str.contains('EKMEK', na=False)]
    if not ekmek.empty:
        print("\n--- EKMEK ODASI DETAY ---")
        print(ekmek.to_string())
    else:
        print("\nEKMEK odasi bulunamadi.")
