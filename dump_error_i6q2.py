import sqlite3
try:
    conn = sqlite3.connect('C:/Projeler/S_program/EKLERİSTAN_QMS/ekleristan_local.db')
    cursor = conn.cursor()
    cursor.execute("SELECT hata_mesaji, stack_trace FROM hata_loglari ORDER BY id DESC LIMIT 1")
    res = cursor.fetchone()
    if res:
        print("MSG:", res[0])
        print("-" * 50)
        print("STACK:", res[1])
    else:
        print("No errors found in DB.")
except Exception as e:
    print(f"Error reading DB: {e}")
