import sqlite3

def verify():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, ad_soyad, bolum, vardiya, servis_duragi, telefon_no FROM personnel ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    
    print(f"Total Rows: {len(rows)}")
    for r in rows:
        print(r)
        
    conn.close()

if __name__ == "__main__":
    import sys
    # Force utf-8 output for safety if redirected
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    verify()
