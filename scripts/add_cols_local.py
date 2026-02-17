import sqlite3

DB_PATH = 'ekleristan_local.db'

def add_columns():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE personel ADD COLUMN telefon_no TEXT")
        print("Added telefon_no")
    except Exception as e:
        print(f"telefon_no error: {e}")

    try:
        cursor.execute("ALTER TABLE personel ADD COLUMN servis_duragi TEXT")
        print("Added servis_duragi")
    except Exception as e:
        print(f"servis_duragi error: {e}")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_columns()
