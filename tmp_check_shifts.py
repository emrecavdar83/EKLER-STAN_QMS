import sqlite3

def check_shifts():
    conn = sqlite3.connect("ekleristan_local.db")
    cursor = conn.cursor()
    print("--- ALL SHIFTS TODAY ---")
    cursor.execute("SELECT * FROM map_vardiya WHERE tarih >= date('now', 'localtime')")
    rows = cursor.fetchall()
    cols = [description[0] for description in cursor.description]
    for r in rows:
        print(dict(zip(cols, r)))
    
    print("\n--- ACTIVE SHIFTS ---")
    cursor.execute("SELECT * FROM map_vardiya WHERE durum='ACIK'")
    rows = cursor.fetchall()
    for r in rows:
        print(dict(zip(cols, r)))
    
    conn.close()

if __name__ == "__main__":
    check_shifts()
