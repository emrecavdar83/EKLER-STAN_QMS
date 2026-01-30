from sqlalchemy import create_engine
import pandas as pd
engine = create_engine('sqlite:///ekleristan_local.db')
print(pd.read_sql("SELECT id, bolum_adi, ana_departman_id FROM ayarlar_bolumler WHERE bolum_adi IN ('DOMBA', 'BOMBA', 'RULO PASTA', 'HALKA TATLI', 'ÜRETİM')", engine))
