
import sqlite3
import pandas as pd

conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(Urun_KPI_Kontrol)")
cols = cursor.fetchall()
with open('kpi_schema_full.txt', 'w', encoding='utf-8') as f:
    for col in cols:
        f.write(f"ID: {col[0]}, Name: {col[1]}, Type: {col[2]}\n")
    
    try:
        df = pd.read_sql("SELECT * FROM Urun_KPI_Kontrol LIMIT 1", conn)
        f.write("\nColumns from DataFrame:\n")
        f.write(str(df.columns.tolist()))
    except:
        f.write("Could not read table data.")

conn.close()
