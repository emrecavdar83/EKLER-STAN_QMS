import sqlite3

def check_personnel_sqlite():
    db_path = 'ekleristan_local.db'
    conn = sqlite3.connect(db_path)
    
    with open('tmp_rulo_result.txt', 'w', encoding='utf-8') as f:
        f.write("--- Rulo Pasta Departmanlar ---\n")
        res = conn.execute("SELECT id, bolum_adi FROM ayarlar_bolumler").fetchall()
        for r in res:
            if 'rulo' in str(r[1]).lower():
                f.write(f"ID: {r[0]}, Bolum: {r[1]}\n")

        f.write("\n--- Rulo Pasta Personelleri ---\n")
        query = """
        SELECT p.id, p.ad_soyad, d.bolum_adi, p.vardiya, p.durum 
        FROM personel p 
        LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id 
        WHERE d.bolum_adi LIKE '%rulo%' OR p.ad_soyad LIKE '%rulo%'
        """
        res = conn.execute(query).fetchall()
        for r in res:
            f.write(f"ID: {r[0]}, Ad: {r[1]}, Bolum: {r[2]}, Vardiya: {r[3]}, Durum: {r[4]}\n")

if __name__ == "__main__":
    check_personnel_sqlite()
