import sqlite3

def find_name(pattern):
    conn = sqlite3.connect('ekleristan_local.db')
    cursor = conn.cursor()
    cursor.execute("SELECT ad_soyad FROM personel WHERE ad_soyad LIKE ?", (f'%{pattern}%',))
    results = cursor.fetchall()
    conn.close()
    return results

if __name__ == "__main__":
    print(f"Searching for ALPASLAN: {find_name('ALPASLAN')}")
    print(f"Searching for ABDULLAH: {find_name('ABDULLAH')}")
    print(f"Searching for ARİF: {find_name('ARİF')}")
