import sqlite3

db_path = 'ekleristan_local.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(personnel)")
columns = cursor.fetchall()

print("Columns in 'personnel' table:")
for col in columns:
    print(col)

conn.close()
