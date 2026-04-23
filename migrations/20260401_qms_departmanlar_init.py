import sqlite3
import datetime


def _tablolari_olustur(cursor):
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qms_departman_turleri (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tur_adi TEXT NOT NULL UNIQUE,
        renk_kodu TEXT,
        aktif INTEGER DEFAULT 1
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qms_departmanlar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kod TEXT, ad TEXT NOT NULL, tur_id INTEGER, ust_id INTEGER,
        lokasyon_kodu TEXT, sira_no INTEGER DEFAULT 0, aktif INTEGER DEFAULT 1,
        olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (tur_id) REFERENCES qms_departman_turleri(id),
        FOREIGN KEY (ust_id) REFERENCES qms_departmanlar(id)
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qms_departman_sorumlulari (
        id INTEGER PRIMARY KEY AUTOINCREMENT, departman_id INTEGER,
        personel_id INTEGER, rol TEXT,
        FOREIGN KEY (departman_id) REFERENCES qms_departmanlar(id),
        FOREIGN KEY (personel_id) REFERENCES personel(id)
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qms_sorumluluk_alanlari (
        id INTEGER PRIMARY KEY AUTOINCREMENT, personel_id INTEGER,
        departman_id INTEGER, notlar TEXT,
        FOREIGN KEY (personel_id) REFERENCES personel(id),
        FOREIGN KEY (departman_id) REFERENCES qms_departmanlar(id)
    )""")
    try:
        cursor.execute("ALTER TABLE personel ADD COLUMN qms_departman_id INTEGER")
    except sqlite3.OperationalError:
        pass


def _tur_tohumla(cursor):
    for ad, renk in [('ÜRETİM','#E74C3C'),('KALİTE','#3498DB'),('OFİS','#95A5A6'),
                     ('TEMİZLİK','#F1C40F'),('DEPO','#E67E22'),('TEKNİK','#2ECC71')]:
        cursor.execute("INSERT OR IGNORE INTO qms_departman_turleri (tur_adi, renk_kodu) VALUES (?, ?)", (ad, renk))
    cursor.execute("SELECT id, tur_adi FROM qms_departman_turleri")
    return {name: tid for tid, name in cursor.fetchall()}


def _org_agaci_tohumla(cursor, type_map):
    def ekle(ad, tur, ust, sira=10):
        cursor.execute("INSERT INTO qms_departmanlar (ad, tur_id, ust_id, sira_no) VALUES (?, ?, ?, ?)",
                       (ad.upper(), type_map.get(tur), ust, sira))
        return cursor.lastrowid

    gm  = ekle('GENEL MÜDÜRLÜK', 'OFİS', None, 1)
    ur  = ekle('ÜRETİM',          'ÜRETİM', gm, 1)
    kal = ekle('KALİTE',           'KALİTE', gm, 3)
    pln = ekle('PLANLAMA',         'OFİS',   gm, 6)
    ekle('İNSAN KAYNAKLARI', 'OFİS',  gm, 2); ekle('MUHASEBE', 'OFİS',  gm, 4)
    ekle('SEVKİYAT',          'DEPO', gm, 5)

    ym = ekle('YARI MAMÜL', 'ÜRETİM', ur); ek = ekle('EKLER', 'ÜRETİM', ur)
    hn = ekle('HACI NADİR', 'ÜRETİM', ur); ok = ekle('OKUL',  'ÜRETİM', ur)
    tm = ekle('TEMİZLİK',  'TEMİZLİK', ur)

    for n in ['KREMA','PANDİSPANYA','PATAŞU']: ekle(n, 'ÜRETİM', ym)
    for n in ['MEYVE','DOLUM','SOS','KREMA','DEKOR','MAP','TERAZİ','MAGNOLYA']: ekle(n, 'ÜRETİM', ek)
    for n in ['TEK PASTA','KURU PASTA','PASTA','BAKLAVA']: ekle(n, 'ÜRETİM', hn)
    for n in ['PROFİTEROL','BOMBA','RULO PASTA']: ekle(n, 'ÜRETİM', ok)
    for n in ['BULAŞIKHANE','TEMİZLİK']: ekle(n, 'TEMİZLİK', tm)
    ekle('İŞ GÜVENLİĞİ', 'KALİTE', kal)
    for n in ['YARI MAMÜL DEPO','MAMÜL DEPO','HAM MADDE DEPO']: ekle(n, 'DEPO', pln)


def migrate():
    conn = sqlite3.connect("ekleristan_local.db")
    cursor = conn.cursor()
    print("Step 1: Creating tables...")
    _tablolari_olustur(cursor)
    print("Step 2: Seeding dynamic types...")
    type_map = _tur_tohumla(cursor)
    print("Step 3: Seeding organizational tree...")
    _org_agaci_tohumla(cursor, type_map)
    conn.commit()
    conn.close()
    print("✅ builder_db: Migration and Seeding successful.")

if __name__ == "__main__":
    migrate()
