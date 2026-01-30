import sqlite3
import os

db_path = 'ekleristan_local.db'

if not os.path.exists(db_path):
    print(f"HATA: {db_path} bulunamadı!")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- LOCAL DB DIAGNOSTICS ---")

# 1. Total Personnel
cursor.execute("SELECT count(*) FROM personel")
total = cursor.fetchone()[0]
print(f"Total Personnel: {total}")

# 2. Active Personnel
# Note: SQLite case insensitivity might handle upper/lower differently than Postgres depending on collation, but we'll try standard SQL
try:
    cursor.execute("SELECT count(*) FROM personel WHERE UPPER(TRIM(durum)) = 'AKTİF'")
    active = cursor.fetchone()[0]
    print(f"Active Personnel: {active}")
except Exception as e:
    print(f"Active Query Error: {e}")

# 3. With Name
cursor.execute("SELECT count(*) FROM personel WHERE ad_soyad IS NOT NULL")
with_name = cursor.fetchone()[0]
print(f"With Name: {with_name}")

# 4. With Dept ID
try:
    cursor.execute("SELECT count(*) FROM personel WHERE departman_id IS NOT NULL")
    with_dept = cursor.fetchone()[0]
    print(f"With Dept ID: {with_dept}")
except:
    print("With Dept ID: Col Missing?")

# 5. Check if 'TAYFUN KORKMAZ' exists (random check, or maybe check for 69th)
print("\nSample records (LIMIT 5):")
cursor.execute("SELECT ad_soyad, durum FROM personel LIMIT 5")
for row in cursor.fetchall():
    print(f"  - {row[0]}: {row[1]}")

conn.close()
