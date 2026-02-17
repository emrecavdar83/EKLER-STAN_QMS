import sqlite3

def check_schema():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(Urun_KPI_Kontrol)")
    columns = cursor.fetchall()
    print(f"Total columns: {len(columns)}")
    for col in columns:
        print(f"ID: {col[0]}, Name: {col[1]}, Type: {col[2]}")
    conn.close()

if __name__ == "__main__":
    check_schema()
