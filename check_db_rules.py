import sqlite3

def check_rules(db_name):
    print(f"--- CHECKING {db_name} ---")
    try:
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        cur.execute("SELECT * FROM soguk_oda_planlama_kurallari WHERE aktif = 1")
        rows = cur.fetchall()
        for r in rows:
            print(r)
        conn.close()
    except Exception as e:
        print(f"Error ({db_name}): {e}")

if __name__ == "__main__":
    check_rules('ekleristan.db')
    check_rules('ekleristan_local.db')
