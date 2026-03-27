import sqlite3

conn = sqlite3.connect('ekleristan_local.db')
cur = conn.cursor()

with open('migrations/20260328_110000_performans_indexleri.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

up_sql = sql.split('-- DOWN MIGRATION')[0]
cur.executescript(up_sql)
conn.commit()
print('Indexler basariyla eklendi.')
conn.close()
