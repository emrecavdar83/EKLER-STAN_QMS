import sqlite3

def check_schema():
    conn = sqlite3.connect('ekleristan_local.db')
    cur = conn.cursor()
    cur.execute("SELECT sql FROM sqlite_master WHERE name='qdms_belgeler'")
    row = cur.fetchone()
    if row:
        print("SCHEMA FOR qdms_belgeler:")
        print(row[0])
    else:
        print("qdms_belgeler table not found.")
    conn.close()

if __name__ == "__main__":
    check_schema()
