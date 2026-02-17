
import sqlite3

try:
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", tables)
    conn.close()
except Exception as e:
    print(e)
