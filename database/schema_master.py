from sqlalchemy import text

def init_all_tables(conn, is_pg):
    """Sistemdeki tüm tabloların kurulumunu koordine eder."""
    _pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    _ts = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if is_pg else "TEXT DEFAULT (datetime('now','localtime'))"
    _if_not_exists = "IF NOT EXISTS"
    
    # 1. Çekirdek Sistem Tabloları
    core_tables = [
        ('sistem_loglari', f"CREATE TABLE {_if_not_exists} sistem_loglari (id {_pk}, islem_tipi VARCHAR(50), detay TEXT, modul VARCHAR(50), kullanici_id INTEGER, detay_json TEXT, ip_adresi VARCHAR(45), cihaz_bilgisi TEXT, zaman {_ts})"),
        ('hata_loglari', f"CREATE TABLE {_if_not_exists} hata_loglari (id {_pk}, hata_kodu VARCHAR(20) UNIQUE NOT NULL, seviye VARCHAR(20) DEFAULT 'ERROR', modul VARCHAR(50), fonksiyon VARCHAR(100), hata_mesaji TEXT NOT NULL, stack_trace TEXT, context_data TEXT, ai_diagnosis TEXT, kullanici_id INTEGER, is_fixed INTEGER DEFAULT 0, zaman {_ts})"),
        ('lokasyon_tipleri', f"CREATE TABLE {_if_not_exists} lokasyon_tipleri (id {_pk}, tip_adi VARCHAR(50) UNIQUE NOT NULL, sira_no INTEGER DEFAULT 10, aktif INTEGER DEFAULT 1)"),
        ('vardiya_tipleri', f"CREATE TABLE {_if_not_exists} vardiya_tipleri (id {_pk}, tip_adi VARCHAR(50) UNIQUE NOT NULL, sira_no INTEGER DEFAULT 10, aktif INTEGER DEFAULT 1, baslangic_saati TEXT, bitis_saati TEXT)"),
        ('qms_departman_turleri', f"""CREATE TABLE {_if_not_exists} qms_departman_turleri (
            id {_pk}, tur_adi VARCHAR(50) UNIQUE NOT NULL, renk_kodu VARCHAR(20), kurallar_json TEXT, sira_no INTEGER DEFAULT 10, durum TEXT DEFAULT 'AKTİF'
        )"""),
        ('qms_departmanlar', f"""CREATE TABLE {_if_not_exists} qms_departmanlar (
            id {_pk}, ad VARCHAR(100) NOT NULL, kod VARCHAR(50), ust_id INTEGER, ikincil_ust_id INTEGER, tur_id INTEGER, yonetici_id INTEGER, dil_anahtari VARCHAR(100), sira_no INTEGER DEFAULT 10, durum TEXT DEFAULT 'AKTİF', guncelleme_tarihi TIMESTAMP,
            FOREIGN KEY (ust_id) REFERENCES qms_departmanlar(id), FOREIGN KEY (ikincil_ust_id) REFERENCES qms_departmanlar(id),
            FOREIGN KEY (tur_id) REFERENCES qms_departman_turleri(id), FOREIGN KEY (yonetici_id) REFERENCES personel(id)
        )"""),
        ('sistem_parametreleri', f"CREATE TABLE {_if_not_exists} sistem_parametreleri (id {_pk}, anahtar VARCHAR(100) UNIQUE NOT NULL, deger TEXT NOT NULL, aciklama TEXT, guncelleme_ts {_ts})"),
    ]

    # 2. Operasyonel ve Personel Tabloları
    op_tables = [
        ('personel_transfer_log', f"""CREATE TABLE {_if_not_exists} personel_transfer_log (
            id {_pk}, personel_id INTEGER NOT NULL, eski_bolum_id INTEGER, yeni_bolum_id INTEGER, islem_yapan_id INTEGER, transfer_tarihi {_ts}, durum TEXT DEFAULT 'BEKLEMEDE', transfer_tipi TEXT, neden TEXT
        )"""),
        ('personel_performans_skorlari', f"""CREATE TABLE {_if_not_exists} personel_performans_skorlari (
            id {_pk}, personel_id INTEGER NOT NULL, donem VARCHAR(20), hijyen_skoru FLOAT DEFAULT 0, hiz_skoru FLOAT DEFAULT 0, kalite_skoru FLOAT DEFAULT 0, genel_skor FLOAT DEFAULT 0, zaman {_ts}, UNIQUE(personel_id, donem)
        )"""),
        ('personel_vardiya_programi', f"""CREATE TABLE {_if_not_exists} personel_vardiya_programi (
            id {_pk}, personel_id INTEGER NOT NULL, baslangic_tarihi TEXT NOT NULL, bitis_tarihi TEXT NOT NULL, vardiya TEXT, izin_gunleri TEXT, aciklama TEXT, onay_durumu TEXT DEFAULT 'ONAYLANDI', onaylayan_id INTEGER, onay_ts {_ts}
        )"""),
        ('birlesik_gorev_havuzu', f"""CREATE TABLE {_if_not_exists} birlesik_gorev_havuzu (
            id {_pk}, personel_id INTEGER NOT NULL, bolum_id INTEGER, gorev_kaynagi VARCHAR(50) NOT NULL, kaynak_id INTEGER NOT NULL, atanma_tarihi DATE NOT NULL, hedef_tarih DATE NOT NULL, durum VARCHAR(50) DEFAULT 'BEKLIYOR', tamamlanma_tarihi DATETIME, onaylayan_id INTEGER
        )"""),
        ('hijyen_kontrol_kayitlari', f"""CREATE TABLE {_if_not_exists} hijyen_kontrol_kayitlari (
            id {_pk}, tarih TEXT NOT NULL, saat TEXT, kullanici TEXT, vardiya TEXT, bolum TEXT, personel TEXT, durum TEXT, sebep TEXT, aksiyon TEXT
        )"""),
    ]

    # 3. MAP ve Performans Tabloları
    map_perf_tables = [
        ('map_vardiya', f"CREATE TABLE {_if_not_exists} map_vardiya (id {_pk}, tarih TEXT NOT NULL, makina_no TEXT NOT NULL DEFAULT 'MAP-01', urun_adi TEXT, vardiya_no INTEGER NOT NULL, baslangic_saati TEXT NOT NULL, bitis_saati TEXT, operator_adi TEXT NOT NULL, vardiya_sefi TEXT, besleme_kisi INTEGER, kasalama_kisi INTEGER, hedef_hiz_paket_dk FLOAT, gerceklesen_uretim INTEGER DEFAULT 0, acan_kullanici_id INTEGER, kapatan_kullanici_id INTEGER, durum TEXT DEFAULT 'ACIK', notlar TEXT, olusturma_ts {_ts}, guncelleme_ts {_ts})"),
        ('map_zaman_cizelgesi', f"CREATE TABLE {_if_not_exists} map_zaman_cizelgesi (id {_pk}, vardiya_id INTEGER NOT NULL, sira_no INTEGER NOT NULL, baslangic_ts TEXT NOT NULL, bitis_ts TEXT, sure_dk FLOAT, durum TEXT NOT NULL, neden TEXT, aciklama TEXT)"),
        ('map_fire_kaydi', f"CREATE TABLE {_if_not_exists} map_fire_kaydi (id {_pk}, vardiya_id INTEGER NOT NULL, fire_tipi TEXT NOT NULL, miktar_adet INTEGER NOT NULL, bobin_ref TEXT, aciklama TEXT, olusturma_ts {_ts})"),
        ('map_bobin_kaydi', f"CREATE TABLE {_if_not_exists} map_bobin_kaydi (id {_pk}, vardiya_id INTEGER NOT NULL, sira_no INTEGER NOT NULL, degisim_ts TEXT NOT NULL, bobin_lot TEXT NOT NULL, film_tipi TEXT DEFAULT 'Üst Film', baslangic_kg FLOAT, bitis_kg FLOAT, kullanilan_kg FLOAT, aciklama TEXT)"),
        ('map_durus_nedenleri', f"CREATE TABLE {_if_not_exists} map_durus_nedenleri (id {_pk}, neden TEXT UNIQUE NOT NULL, aktif INTEGER DEFAULT 1)"),
        ('map_fire_tipleri', f"CREATE TABLE {_if_not_exists} map_fire_tipleri (id {_pk}, fire_tipi TEXT UNIQUE NOT NULL, aktif INTEGER DEFAULT 1)"),
    ]

    # Tüm listeleri birleştir ve çalıştır
    all_sql_lists = [core_tables, op_tables, map_perf_tables]
    for sql_list in all_sql_lists:
        for t_name, t_sql in sql_list:
            try:
                conn.execute(text(t_sql))
            except Exception as e:
                print(f"Table Error ({t_name}): {e}")
    
    # 4. Güvenlik Sıkılaştırması (Supabase RLS)
    if is_pg:
        _apply_rls_hardening(conn)

def _apply_rls_hardening(conn):
    """PostgreSQL için tüm public tablolarında RLS'yi aktif eder."""
    try:
        # public şemasındaki tüm tabloları al
        sql_list = text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
        tables = conn.execute(sql_list).fetchall()
        
        for r in tables:
            t_name = r[0]
            # owner bypass eder, anon/authenticated rolleri için default deny sağlar
            conn.execute(text(f'ALTER TABLE "{t_name}" ENABLE ROW LEVEL SECURITY'))
    except Exception as e:
        print(f"RLS Hardening Error: {e}")

def init_performans_tables(conn, is_pg):
    """Performans ve Polivalans tablolarını kurar."""
    _pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    _ts = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if is_pg else "TEXT DEFAULT (datetime('now','localtime'))"
    
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS performans_degerledirme (
            id {_pk}, uuid TEXT UNIQUE NOT NULL, personel_id INTEGER, calisan_adi_soyadi TEXT NOT NULL, bolum TEXT NOT NULL, gorevi TEXT NOT NULL, ise_giris_tarihi DATE,
            donem TEXT NOT NULL, degerlendirme_tarihi DATE NOT NULL, degerlendirme_yili INTEGER NOT NULL, agirlikli_toplam_puan REAL NOT NULL, polivalans_duzeyi TEXT NOT NULL, polivalans_kodu INTEGER NOT NULL,
            olusturma_tarihi {_ts}, guncelleyen_kullanici TEXT, surum INTEGER DEFAULT 1, silinmis INTEGER DEFAULT 0
        )
    """))
    
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS polivalans_matris (
            id {_pk}, personel_id INTEGER, calisan_adi TEXT NOT NULL, bolum TEXT NOT NULL, gorevi TEXT NOT NULL, guncelleme_yili INTEGER NOT NULL,
            yil_ortalama REAL, polivalans_kodu INTEGER, polivalans_metni TEXT, olusturma_tarihi {_ts}
        )
    """))
    
    # Performans tabloları için de RLS uygula
    if is_pg:
        _apply_rls_hardening(conn)
