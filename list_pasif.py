import sqlite3

def list_pasif():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    target_depts = ('BOMBA', 'PROFİTEROL', 'RULO PASTA')
    cursor.execute("SELECT ad_soyad, bolum FROM personel WHERE (durum = 'Pasif' OR durum = 'PASİF') AND bolum IN (?, ?, ?)", target_depts)
    rows = cursor.fetchall()
    
    print("SİSTEMDE PASİF DURUMDA OLANLAR:")
    for row in rows:
        print(f"- {row[0]} ({row[1]})")
        
    conn.close()

if __name__ == "__main__":
    list_pasif()
