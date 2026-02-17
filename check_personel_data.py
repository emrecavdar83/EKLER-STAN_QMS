
import sqlite3
import pandas as pd

conn = sqlite3.connect('ekleristan_local.db')
print("--- Personel Table Schema ---")
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(personel)")
cols = cursor.fetchall()
for col in cols:
    print(col)

print("\n--- Sample Data (Shift and Role) ---")
df = pd.read_sql("SELECT ad_soyad, rol, vardiya, durum, departman_id FROM personel LIMIT 20", conn)
print(df)

print("\n--- Vardiya Values ---")
df_v = pd.read_sql("SELECT DISTINCT vardiya FROM personel", conn)
print(df_v)

print("\n--- Rol Values ---")
df_r = pd.read_sql("SELECT DISTINCT rol FROM personel", conn)
print(df_r)

conn.close()
