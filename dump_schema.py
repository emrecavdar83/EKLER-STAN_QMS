import sqlite3
import pandas as pd

conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]

print("Database Schema Details:")
for table in tables:
    print(f"\n--- Table: {table} ---")
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table}';")
    print(cursor.fetchone()[0])

conn.close()
