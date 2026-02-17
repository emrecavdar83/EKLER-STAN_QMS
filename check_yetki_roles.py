
import pandas as pd
from sqlalchemy import create_engine

local_engine = create_engine('sqlite:///ekleristan_local.db')

with local_engine.connect() as conn:
    df = pd.read_sql("SELECT DISTINCT rol_adi FROM ayarlar_yetkiler", conn)
    print("Distinct roles in ayarlar_yetkiler:")
    for r in df['rol_adi']:
        print(f"'{r}'")
