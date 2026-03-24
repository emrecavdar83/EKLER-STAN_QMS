import sqlite3

def check_schema():
    conn = sqlite3.connect('ekleristan_local.db')
    cur = conn.cursor()
    cur.execute("SELECT sql FROM sqlite_master WHERE name='qdms_belgeler'")
    row = cur.fetchone()
    with open('qdms_schema.txt', 'w', encoding='utf-8') as f:
        if row:
            f.write(row[0])
        else:
            f.write("Table not found")
    conn.close()

if __name__ == "__main__":
    check_schema()
