import sqlite3

try:
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM personel WHERE ad_soyad LIKE '%GEM%'")
    rows = cursor.fetchall()
    cols = [description[0] for description in cursor.description]
    for row in rows:
        print(dict(zip(cols, row)))
except Exception as e:
    print(e)
