import sqlite3

def check():
    conn = sqlite3.connect('ekleristan_local.db')
    cur = conn.cursor()
    
    names = ['AHMAD KOURANI', 'HASSAN HABRA', 'MUSTAFA AVŞAR']
    
    print(f"{'ID':<5} | {'Ad Soyad':<25} | {'Vardiya'}")
    print("-" * 50)
    
    for name in names:
        cur.execute("SELECT id, ad_soyad, vardiya FROM personnel WHERE ad_soyad LIKE ?", (f"%{name}%",))
        rows = cur.fetchall()
        for row in rows:
            print(f"{row[0]:<5} | {row[1]:<25} | {row[2]}")
            
    conn.close()

if __name__ == "__main__":
    check()
