import sqlite3
import datetime

def migrate():
    db_path = "ekleristan_local.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Step 1: Creating tables...")
    
    # 1. Departman Türleri (Dinamiklik İlkesi)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qms_departman_turleri (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tur_adi TEXT NOT NULL UNIQUE,
        renk_kodu TEXT,
        aktif INTEGER DEFAULT 1
    )
    """)
    
    # 2. Departmanlar
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qms_departmanlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kod TEXT,
        ad TEXT NOT NULL,
        tur_id INTEGER,
        ust_id INTEGER,
        lokasyon_kodu TEXT,
        sira_no INTEGER DEFAULT 0,
        aktif INTEGER DEFAULT 1,
        olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tur_id) REFERENCES qms_departman_turleri(id),
        FOREIGN KEY (ust_id) REFERENCES qms_departmanlar(id)
    )
    """)
    
    # 3. Sorumlular ve Alanlar
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qms_departman_sorumlulari (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        departman_id INTEGER,
        personel_id INTEGER,
        rol TEXT,
        FOREIGN KEY (departman_id) REFERENCES qms_departmanlar(id),
        FOREIGN KEY (personel_id) REFERENCES personel(id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qms_sorumluluk_alanlari (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        personel_id INTEGER,
        departman_id INTEGER,
        notlar TEXT,
        FOREIGN KEY (personel_id) REFERENCES personel(id),
        FOREIGN KEY (departman_id) REFERENCES qms_departmanlar(id)
    )
    """)
    
    try:
        cursor.execute("ALTER TABLE personel ADD COLUMN qms_departman_id INTEGER")
    except sqlite3.OperationalError:
        pass
        
    print("Step 2: Seeding dynamic types...")
    types = [
        ('ÜRETİM', '#E74C3C'),
        ('KALİTE', '#3498DB'),
        ('OFİS', '#95A5A6'),
        ('TEMİZLİK', '#F1C40F'),
        ('DEPO', '#E67E22'),
        ('TEKNİK', '#2ECC71')
    ]
    for t_name, t_color in types:
        cursor.execute("INSERT OR IGNORE INTO qms_departman_turleri (tur_adi, renk_kodu) VALUES (?, ?)", (t_name, t_color))
    
    # Get type IDs
    cursor.execute("SELECT id, tur_adi FROM qms_departman_turleri")
    type_map = {name: id for id, name in cursor.fetchall()}
    
    print("Step 3: Seeding organizational tree...")
    
    def add_dept(ad, tur_name, parent_id, sira=10):
        tid = type_map.get(tur_name)
        cursor.execute("INSERT INTO qms_departmanlar (ad, tur_id, ust_id, sira_no) VALUES (?, ?, ?, ?)", (ad.upper(), tid, parent_id, sira))
        return cursor.lastrowid

    # Root
    genel_mudurluk_id = add_dept('GENEL MÜDÜRLÜK', 'OFİS', None, 1)
    
    # Level 2
    uretim_id = add_dept('ÜRETİM', 'ÜRETİM', genel_mudurluk_id, 1)
    ik_id = add_dept('İNSAN KAYNAKLARI', 'OFİS', genel_mudurluk_id, 2)
    kalite_id = add_dept('KALİTE', 'KALİTE', genel_mudurluk_id, 3)
    muhasebe_id = add_dept('MUHASEBE', 'OFİS', genel_mudurluk_id, 4)
    sevkiyat_id = add_dept('SEVKİYAT', 'DEPO', genel_mudurluk_id, 5)
    planlama_id = add_dept('PLANLAMA', 'OFİS', genel_mudurluk_id, 6)
    
    # Level 3 - Üretim
    yari_mamul_id = add_dept('YARI MAMÜL', 'ÜRETİM', uretim_id)
    ekler_id = add_dept('EKLER', 'ÜRETİM', uretim_id)
    haci_nadir_id = add_dept('HACI NADİR', 'ÜRETİM', uretim_id)
    okul_id = add_dept('OKUL', 'ÜRETİM', uretim_id)
    temizlik_id = add_dept('TEMİZLİK', 'TEMİZLİK', uretim_id)
    
    # Level 4 - Sub-production
    for n in ['KREMA', 'PANDİSPANYA', 'PATAŞU']: add_dept(n, 'ÜRETİM', yari_mamul_id)
    for n in ['MEYVE', 'DOLUM', 'SOS', 'KREMA', 'DEKOR', 'MAP', 'TERAZİ', 'MAGNOLYA']: add_dept(n, 'ÜRETİM', ekler_id)
    for n in ['TEK PASTA', 'KURU PASTA', 'PASTA', 'BAKLAVA']: add_dept(n, 'ÜRETİM', haci_nadir_id)
    for n in ['PROFİTEROL', 'BOMBA', 'RULO PASTA']: add_dept(n, 'ÜRETİM', okul_id)
    for n in ['BULAŞIKHANE', 'TEMİZLİK']: add_dept(n, 'TEMİZLİK', temizlik_id)
    
    # Rest
    add_dept('İŞ GÜVENLİĞİ', 'KALİTE', kalite_id)
    for n in ['YARI MAMÜL DEPO', 'MAMÜL DEPO', 'HAM MADDE DEPO']: add_dept(n, 'DEPO', planlama_id)
    
    conn.commit()
    conn.close()
    print("✅ builder_db: Migration and Seeding successful.")

if __name__ == "__main__":
    migrate()
