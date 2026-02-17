import pandas as pd
import sqlite3

conn = sqlite3.connect('ekleristan_local.db')

print('--- EZEL ---')
df_ezel = pd.read_sql("SELECT * FROM personel WHERE ad_soyad LIKE '%EZEL%'", conn)
print(df_ezel)

print('\n--- BOLUMLER ---')
df_dept = pd.read_sql("SELECT id, bolum_adi FROM ayarlar_bolumler", conn)
print(df_dept)

conn.close()
