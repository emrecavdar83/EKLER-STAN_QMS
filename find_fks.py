import sqlite3

conn = sqlite3.connect('ekleristan_local.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]

print("Tables referencing 'personel':")
for table in tables:
    cursor.execute(f"PRAGMA foreign_key_list({table});")
    fks = cursor.fetchall()
    for fk in fks:
        # fk structure: (id, seq, table, from, to, on_update, on_delete, match)
        referenced_table = fk[2]
        if referenced_table.lower() == 'personel':
            print(f"Table: {table}, FK: {fk[3]} -> {fk[4]}, ON DELETE: {fk[6]}")

conn.close()
