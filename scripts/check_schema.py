import sqlite3

def check_schema():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    print("--- Tables ---")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(tables)
    
    print("\n--- Personnel Columns ---")
    cursor.execute("PRAGMA table_info(personnel);")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
        
    conn.close()

if __name__ == "__main__":
    check_schema()
