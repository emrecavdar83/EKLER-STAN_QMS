import sqlite3

def recreate_tasks():
    conn = sqlite3.connect('ekleristan_local.db')
    cur = conn.cursor()
    
    # Drop existing (if exists)
    cur.execute("DROP TABLE IF EXISTS birlesik_gorev_havuzu")
    
    # Create with new FK to qms_departmanlar
    sql = """
    CREATE TABLE birlesik_gorev_havuzu (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        personel_id INTEGER NOT NULL,
        bolum_id INTEGER, -- QMS Departman ID
        gorev_kaynagi VARCHAR(50) NOT NULL, -- PERIYODIK, AKILLI_AKIS, QDMS, DOF, YONETIM vs.
        kaynak_id INTEGER NOT NULL,
        atanma_tarihi DATE NOT NULL,
        hedef_tarih DATE NOT NULL,
        durum VARCHAR(50) DEFAULT 'BEKLIYOR',
        tamamlanma_tarihi DATETIME,
        sapma_notu TEXT,
        onaylayan_id INTEGER,
        FOREIGN KEY (personel_id) REFERENCES personel(id),
        FOREIGN KEY (bolum_id) REFERENCES qms_departmanlar(id),
        FOREIGN KEY (onaylayan_id) REFERENCES personel(id),
        UNIQUE(personel_id, gorev_kaynagi, kaynak_id, hedef_tarih)
    )
    """
    cur.execute(sql)
    conn.commit()
    print("birlesik_gorev_havuzu recreated successfully.")
    conn.close()

if __name__ == "__main__":
    recreate_tasks()
