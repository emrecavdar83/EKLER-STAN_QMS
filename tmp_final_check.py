import sqlite3
import datetime

def check_results():
    conn = sqlite3.connect('ekleristan_local.db')
    c = conn.cursor()
    
    print("=== FINAL PLAN STATUS ===")
    c.execute("""
        SELECT o.id, o.oda_adi, COUNT(p.id) 
        FROM soguk_odalar o 
        LEFT JOIN olcum_plani p ON o.id = p.oda_id 
        WHERE o.aktif = 1
        GROUP BY o.id, o.oda_adi
    """)
    for r in c.fetchall():
        print(f"Room ID={r[0]} | Name={r[1]} | Slots={r[2]}")

    print("\n=== RECENT RECORDS CHECK ===")
    c.execute("""
        SELECT o.oda_adi, s.olcum_zamani, s.sicaklik_degeri 
        FROM sicaklik_olcumleri s 
        JOIN soguk_odalar o ON s.oda_id = o.id 
        ORDER BY s.olcum_zamani DESC LIMIT 5
    """)
    for r in c.fetchall():
        print(f"Record: {r[0]} | Time: {r[1]} | Temp: {r[2]}")

if __name__ == "__main__":
    check_results()
