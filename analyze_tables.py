import sqlite3
import pandas as pd

conn = sqlite3.connect('ekleristan_local.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()

print("Mevcut Tablo Sayisi:", len(tables))
print("-" * 30)

summary = []
for t in tables:
    table_name = t[0]
    # Skip sqlite internal tables
    if table_name.startswith('sqlite_'): continue
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cur.fetchone()[0]
        summary.append({'Tablo': table_name, 'Satir_Sayisi': count})
    except:
        pass

df = pd.DataFrame(summary).sort_values(by='Satir_Sayisi', ascending=False)
print(df.to_string(index=False))
conn.close()
