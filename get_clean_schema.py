import sqlite3

conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()

def get_schema(table_name):
    cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    result = cursor.fetchone()
    return result[0] if result else f"Table {table_name} not found"

print("PERSONEL TABLE SCHEMA:")
print(get_schema('personel'))

print("\nPERSONEL_VARDIYA_PROGRAMI TABLE SCHEMA:")
print(get_schema('personel_vardiya_programi'))

conn.close()
