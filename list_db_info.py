import sqlite3

import sqlite3

def list_db_info():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    # Try to fetch departments
    if 'ayarlar_bolumler' in tables:
        cursor.execute("PRAGMA table_info(ayarlar_bolumler)")
        print("\nColumns in ayarlar_bolumler:", [row[1] for row in cursor.fetchall()])
        cursor.execute("SELECT * FROM ayarlar_bolumler")
        print("Departments (ayarlar_bolumler):")
        for row in cursor.fetchall():
            print(row)
            
    # Fetch personnel
    if 'personel' in tables:
        cursor.execute("PRAGMA table_info(personel)")
        cols = [row[1] for row in cursor.fetchall()]
        print(f"\nColumns in personel: {cols}")
        
        cursor.execute("SELECT * FROM personel")
        print("Existing Personnel:")
        for row in cursor.fetchall():
            print(row)
            
    conn.close()
            
    conn.close()

if __name__ == "__main__":
    list_db_info()
