import sqlite3

def list_personnel():
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    
    target_depts = ('BOMBA', 'PROFİTEROL', 'RULO PASTA')
    cursor.execute("SELECT ad_soyad, bolum, durum FROM personel WHERE bolum IN (?, ?, ?)", target_depts)
    rows = cursor.fetchall()
    
    with open('full_list_utf8.txt', 'w', encoding='utf-8') as f:
        f.write(f"{'İsim':<30} | {'Bölüm':<15} | {'Durum':<10}\n")
        f.write("-" * 60 + "\n")
        for row in rows:
            f.write(f"{row[0]:<30} | {row[1]:<15} | {row[2]:<10}\n")
        
    conn.close()

if __name__ == "__main__":
    list_personnel()
