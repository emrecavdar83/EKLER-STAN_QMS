import sqlite3
import pandas as pd
conn = sqlite3.connect('C:/Projeler/S_program/EKLERİSTAN_QMS/ekleristan_local.db')

tables = ['temizlik_kayitlari', 'hijyen_kontrol_kayitlari', 'depo_giris_kayitlari']
for t in tables:
    try:
        df = pd.read_sql(f'PRAGMA table_info({t})', conn)
        print(f'--- {t} ---')
        for idx, row in df.iterrows():
            print(f'  - {row["name"]}')
    except Exception as e:
        print(f'Hata {t}: {e}')
