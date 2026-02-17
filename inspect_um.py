
import pandas as pd
from sqlalchemy import create_engine

local_engine = create_engine('sqlite:///ekleristan_local.db')

with local_engine.connect() as conn:
    df = pd.read_sql("SELECT * FROM ayarlar_yetkiler WHERE rol_adi = 'ÜRETİM MÜDÜRÜ'", conn)
    print(df.to_string())
