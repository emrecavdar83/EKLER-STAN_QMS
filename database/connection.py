import streamlit as st
from sqlalchemy import create_engine, text

def _create_engine_internal():
    """Bağlantı motorunu fiziksel olarak oluşturur."""
    db_url = None
    if "DB_URL" in st.secrets:
        db_url = st.secrets["DB_URL"]
    elif "streamlit" in st.secrets and "DB_URL" in st.secrets["streamlit"]:
        db_url = st.secrets["streamlit"]["DB_URL"]
    
    if db_url:
        # ANAYASA v3.0: Supabase/Cloud Optimizasyonu (EKL-PERF-002)
        engine = create_engine(
            db_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True, 
            pool_recycle=1800,
            connect_args={"connect_timeout": 10}
        )
        
        if 'postgresql' in db_url:
            from sqlalchemy import event
            @event.listens_for(engine, "connect")
            def set_postgresql_tz(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("SET TIMEZONE='Europe/Istanbul'")
                cursor.close()
        return engine
    else:
        db_url = 'sqlite:///ekleristan_local.db'
        engine = create_engine(db_url, connect_args={'check_same_thread': False})
        from sqlalchemy import event
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
        return engine

@st.cache_resource
def get_engine():
    """Anayasa v3.3: Tek giriş noktası, Cache-Resource garantili."""
    eng = _create_engine_internal()
    is_pg = eng.dialect.name == 'postgresql'
    
    # Tüm bakımı tek bir AUTOCOMMIT bağlantısı üzerinden yapalım (PG için kritik)
    maint_eng = eng.execution_options(isolation_level="AUTOCOMMIT") if is_pg else eng
    
    try:
        with maint_eng.connect() as conn:
            # 1. Şema ve Kritik Veri (Bağlantı paslayarak)
            try: _ensure_schema_sync_with_conn(conn, is_pg)
            except Exception as e: print(f"SCHEMA_SYNC_ERR: {e}")
            
            try: _ensure_critical_data_with_conn(conn, is_pg)
            except Exception as e: print(f"CRITICAL_DATA_ERR: {e}")
            
            try: _ensure_admin_account_with_conn(conn, is_pg)
            except Exception as e: print(f"ADMIN_ACCOUNT_ERR: {e}")
            
            # 2. Modül Başlatıcılar (Orijinal engine üzerinden ama maint_eng etkisiyle)
            try:
                from database.schema_qdms import init_qdms_tables
                init_qdms_tables(maint_eng) # Artık bu da AUTOCOMMIT modunda çalışacak
            except Exception as e:
                print(f"QDMS Schema Init Error: {e}")

            try:
                from soguk_oda_utils import init_sosts_tables
                init_sosts_tables(maint_eng) # Artık bu da AUTOCOMMIT modunda çalışacak
            except: pass
        
    except Exception as e:
        # v4.3.3: SILENT SHIELD - Bakım hatası sayfa açılışını ENGELLEMEZ
        print(f"📛 MAINTENANCE_CRITICAL_FAILURE: {e}")
    return eng

def _ensure_schema_sync_with_conn(conn, is_pg):
    """Kritik şema göçlerini (migration) yönetir."""
    # Şemaları çek
    res_cols = _get_existing_columns(conn, is_pg)
    existing_cols = {(r[0].lower(), r[1].lower()) for r in res_cols}
    
    mig_list = _get_migration_list()
    for tbl, col, sql in mig_list:
        if (tbl, col) not in existing_cols:
            try:
                # SQLite için transaction gerekebilir (PG zaten AUTOCOMMIT'te)
                conn.execute(text(sql))
            except Exception as e:
                print(f"Migration Error ({tbl}): {e}")

def _get_existing_columns(conn, is_pg):
    if is_pg:
        return conn.execute(text("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public'")).fetchall()
    # SQLite: Tüm tablolar için kolon listesini çek (Dinamik ve v3.3 sonrası güvenli)
    all_cols = []
    try:
        tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
        for t_row in tables:
            t_name = t_row[0]
            c_res = conn.execute(text(f"PRAGMA table_info({t_name})")).fetchall()
            for c in c_res:
                all_cols.append((t_name, c[1]))
    except Exception as e:
        print(f"Schema Check Error (SQLite): {e}")
    return all_cols

def _get_migration_list():
    return [
        ("urun_kpi_kontrol", "fotograf_b64", "ALTER TABLE urun_kpi_kontrol ADD COLUMN fotograf_b64 TEXT"),
        ("sicaklik_olcumleri", "planlanan_zaman", "ALTER TABLE sicaklik_olcumleri ADD COLUMN planlanan_zaman TIMESTAMP"),
        ("sicaklik_olcumleri", "qr_ile_girildi", "ALTER TABLE sicaklik_olcumleri ADD COLUMN qr_ile_girildi INTEGER DEFAULT 1"),
        ("ayarlar_roller", "aktif", "ALTER TABLE ayarlar_roller ADD COLUMN aktif INTEGER DEFAULT 1"),
        ("personel", "guncelleme_tarihi", "ALTER TABLE personel ADD COLUMN guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        # v3.5: BRCGS Columns for Documents
        ("qdms_belgeler", "amac", "ALTER TABLE qdms_belgeler ADD COLUMN amac TEXT"),
        ("qdms_belgeler", "kapsam", "ALTER TABLE qdms_belgeler ADD COLUMN kapsam TEXT"),
        ("qdms_belgeler", "tanimlar", "ALTER TABLE qdms_belgeler ADD COLUMN tanimlar TEXT"),
        ("qdms_belgeler", "dokumanlar", "ALTER TABLE qdms_belgeler ADD COLUMN dokumanlar TEXT"),
        ("qdms_belgeler", "icerik", "ALTER TABLE qdms_belgeler ADD COLUMN icerik TEXT"),
        # v3.6: GK Discipline Expansion
        ("qdms_gk_sorumluluklar", "disiplin_tipi", "ALTER TABLE qdms_gk_sorumluluklar ADD COLUMN disiplin_tipi TEXT"),
        ("qdms_gk_sorumluluklar", "etkilesim_birimleri", "ALTER TABLE qdms_gk_sorumluluklar ADD COLUMN etkilesim_birimleri TEXT"),
        # v4.0.3: Restoring MAP Schema Gaps (EKL-MAP-FIX-001)
        ("map_vardiya", "vardiya_sefi", "ALTER TABLE map_vardiya ADD COLUMN vardiya_sefi TEXT"),
        ("map_vardiya", "besleme_kisi", "ALTER TABLE map_vardiya ADD COLUMN besleme_kisi INTEGER"),
        ("map_vardiya", "kasalama_kisi", "ALTER TABLE map_vardiya ADD COLUMN kasalama_kisi INTEGER"),
        ("map_vardiya", "hedef_hiz_paket_dk", "ALTER TABLE map_vardiya ADD COLUMN hedef_hiz_paket_dk FLOAT"),
        ("map_vardiya", "gerceklesen_uretim", "ALTER TABLE map_vardiya ADD COLUMN gerceklesen_uretim INTEGER DEFAULT 0"),
        ("map_vardiya", "notlar", "ALTER TABLE map_vardiya ADD COLUMN notlar TEXT"),
        # v4.0.6: Phase 2.2 Global Activity Tracker expansion
        ("sistem_loglari", "modul", "ALTER TABLE sistem_loglari ADD COLUMN modul VARCHAR(50)"),
        ("sistem_loglari", "kullanici_id", "ALTER TABLE sistem_loglari ADD COLUMN kullanici_id INTEGER"),
        ("sistem_loglari", "detay_json", "ALTER TABLE sistem_loglari ADD COLUMN detay_json TEXT"),
        ("sistem_loglari", "ip_adresi", "ALTER TABLE sistem_loglari ADD COLUMN ip_adresi VARCHAR(45)"),
        ("sistem_loglari", "cihaz_bilgisi", "ALTER TABLE sistem_loglari ADD COLUMN cihaz_bilgisi TEXT"),
        # v5.8.1: Personel & Transfer & Performans Expansion
        ("personel", "baslama_tarihi", "ALTER TABLE personel ADD COLUMN baslama_tarihi DATE"),
        ("personel", "vekil_id", "ALTER TABLE personel ADD COLUMN vekil_id INTEGER"),
        ("personel", "aktif_izinde_mi", "ALTER TABLE personel ADD COLUMN aktif_izinde_mi INTEGER DEFAULT 0"),
        ("ayarlar_roller", "min_seviye", "ALTER TABLE ayarlar_roller ADD COLUMN min_seviye INTEGER"),
        ("ayarlar_roller", "max_seviye", "ALTER TABLE ayarlar_roller ADD COLUMN max_seviye INTEGER"),
        # v5.8.2: Dynamic Shift Hours & Termination Info (EKL-PERS-HARD-001)
        ("vardiya_tipleri", "baslangic_saati", "ALTER TABLE vardiya_tipleri ADD COLUMN baslangic_saati TEXT"),
        ("vardiya_tipleri", "bitis_saati", "ALTER TABLE vardiya_tipleri ADD COLUMN bitis_saati TEXT"),
        ("personel", "ayrilma_tarihi", "ALTER TABLE personel ADD COLUMN ayrilma_tarihi DATE"),
        ("personel", "ayrilma_nedeni", "ALTER TABLE personel ADD COLUMN ayrilma_nedeni TEXT"),
        # v5.9.0: zone_yetki.py için zorunlu kolon
        ("ayarlar_yetkiler", "eylem_yetkileri", "ALTER TABLE ayarlar_yetkiler ADD COLUMN eylem_yetkileri TEXT"),
        # v6.1.0: QMS Departman Hiyerarşisi (Cloud Sync)
        ("personel", "qms_departman_id", "ALTER TABLE personel ADD COLUMN qms_departman_id INTEGER"),
        ("qms_departmanlar", "yonetici_id", "ALTER TABLE qms_departmanlar ADD COLUMN yonetici_id INTEGER"),
    ]


def _ensure_schema_sync_with_conn(conn, is_pg):
    """Anayasa v5.8.1: Veritabanı şemasını otomatik olarak senkronize eder (Dinamik Migration)."""
    # v6.3.1: Agresif Manuel Onarım (Eğer kolon tespiti başarısız olduysa - P0 Hotfix)
    if is_pg:
        for col, col_type in [("ikincil_ust_id", "INTEGER"), ("kod", "VARCHAR(50)"), ("dil_anahtari", "VARCHAR(100)"), ("yonetici_id", "INTEGER")]:
            try:
                conn.execute(text(f"ALTER TABLE qms_departmanlar ADD COLUMN IF NOT EXISTS {col} {col_type}"))
            except Exception: pass
    
    res_cols = _get_existing_columns(conn, is_pg)



def _ensure_critical_data_with_conn(conn, is_pg):
    """Sabit verileri ve sistem tablolarını garanti eder."""
    res_tabs = _get_existing_tables(conn, is_pg)
    existing_tables = {r[0].lower() for r in res_tabs}

    _ensure_system_tables(conn, existing_tables, is_pg)
    _ensure_vardiya_programi_table(conn, existing_tables, is_pg)
    _cleanup_old_logs(conn, is_pg)
    _create_map_performance_tables(conn, existing_tables, is_pg)
    _create_performans_tables(conn, existing_tables, is_pg)
    _bootstrap_modules(conn, is_pg)
    _run_naming_migration_with_conn(conn, is_pg)
    _bootstrap_performans_yetkiler(conn, is_pg)
    _bootstrap_qms_departments(conn, is_pg)

def _get_existing_tables(conn, is_pg):
    if is_pg:
        return conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
    return conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()

def _ensure_system_tables(conn, existing_tables, is_pg):
    _pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    _ts = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if is_pg else "TEXT DEFAULT (datetime('now','localtime'))"
    _if_not_exists = "IF NOT EXISTS"
    
    sistem_tablolari = [
        ('sistem_loglari', f"CREATE TABLE {_if_not_exists} sistem_loglari (id {_pk}, islem_tipi VARCHAR(50), detay TEXT, modul VARCHAR(50), kullanici_id INTEGER, detay_json TEXT, ip_adresi VARCHAR(45), cihaz_bilgisi TEXT, zaman TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"),
        ('hata_loglari', f"CREATE TABLE {_if_not_exists} hata_loglari (id {_pk}, hata_kodu VARCHAR(20) UNIQUE NOT NULL, seviye VARCHAR(20) DEFAULT 'ERROR', modul VARCHAR(50), fonksiyon VARCHAR(100), hata_mesaji TEXT NOT NULL, stack_trace TEXT, context_data TEXT, ai_diagnosis TEXT, kullanici_id INTEGER, is_fixed INTEGER DEFAULT 0, zaman {_ts})"),
        ('lokasyon_tipleri', f"CREATE TABLE {_if_not_exists} lokasyon_tipleri (id {_pk}, tip_adi VARCHAR(50) UNIQUE NOT NULL, sira_no INTEGER DEFAULT 10, aktif INTEGER DEFAULT 1)"),
        ('vardiya_tipleri', f"CREATE TABLE {_if_not_exists} vardiya_tipleri (id {_pk}, tip_adi VARCHAR(50) UNIQUE NOT NULL, sira_no INTEGER DEFAULT 10, aktif INTEGER DEFAULT 1)"),
        ('personel_transfer_log', f"""CREATE TABLE {_if_not_exists} personel_transfer_log (
            id {_pk}, 
            personel_id INTEGER NOT NULL, 
            eski_bolum_id INTEGER, 
            yeni_bolum_id INTEGER, 
            islem_yapan_id INTEGER, 
            transfer_tarihi {_ts}, 
            eski_yonetici_onay_ts TEXT, 
            yeni_yonetici_onay_ts TEXT, 
            durum TEXT DEFAULT 'BEKLEMEDE', 
            transfer_tipi TEXT, 
            neden TEXT
        )"""),
        ('personel_performans_skorlari', f"""CREATE TABLE personel_performans_skorlari (
            id {_pk}, 
            personel_id INTEGER NOT NULL, 
            donem VARCHAR(20), 
            hijyen_skoru FLOAT DEFAULT 0, 
            hiz_skoru FLOAT DEFAULT 0, 
            kalite_skoru FLOAT DEFAULT 0, 
            genel_skor FLOAT DEFAULT 0, 
            zaman {_ts},
            UNIQUE(personel_id, donem)
        )"""),
        ('personel_vardiya_istisnalari', f"""CREATE TABLE {_if_not_exists} personel_vardiya_istisnalari (
            id {_pk},
            personel_id INTEGER NOT NULL,
            tarih DATE NOT NULL,
            yeni_vardiya_id INTEGER,
            neden TEXT,
            islem_yapan_id INTEGER,
            zaman {_ts}
        )"""),
        ('birlesik_gorev_havuzu', f"""CREATE TABLE {_if_not_exists} birlesik_gorev_havuzu (
            id {_pk},
            personel_id INTEGER NOT NULL,
            bolum_id INTEGER,
            gorev_kaynagi VARCHAR(50) NOT NULL,
            kaynak_id INTEGER NOT NULL,
            atanma_tarihi DATE NOT NULL,
            hedef_tarih DATE NOT NULL,
            durum VARCHAR(50) DEFAULT 'BEKLIYOR',
            tamamlanma_tarihi DATETIME,
            sapma_notu TEXT,
            onaylayan_id INTEGER,
            FOREIGN KEY (personel_id) REFERENCES personel(id),
            FOREIGN KEY (onaylayan_id) REFERENCES personel(id)
        )"""),
        ('qms_departman_turleri', f"""CREATE TABLE {_if_not_exists} qms_departman_turleri (
            id {_pk},
            tur_adi VARCHAR(50) UNIQUE NOT NULL,
            sira_no INTEGER DEFAULT 10,
            aktif INTEGER DEFAULT 1
        )"""),
        ('qms_departmanlar', f"""CREATE TABLE {_if_not_exists} qms_departmanlar (
            id {_pk},
            ad VARCHAR(100) NOT NULL,
            kod VARCHAR(50),
            ust_id INTEGER,
            ikincil_ust_id INTEGER,
            tur_id INTEGER,
            yonetici_id INTEGER,
            dil_anahtari VARCHAR(100),
            sira_no INTEGER DEFAULT 10,
            aktif INTEGER DEFAULT 1,
            FOREIGN KEY (ust_id) REFERENCES qms_departmanlar(id),
            FOREIGN KEY (ikincil_ust_id) REFERENCES qms_departmanlar(id),
            FOREIGN KEY (tur_id) REFERENCES qms_departman_turleri(id),
            FOREIGN KEY (yonetici_id) REFERENCES personel(id)
        )""")
    ]
    for t_name, t_sql in sistem_tablolari:
        # v6.1.1: Always try to execute with IF NOT EXISTS for resilience
        try:
            conn.execute(text(t_sql))
        except Exception as e:
            print(f"Sistem Tablo Hatası ({t_name}): {e}")

def _ensure_vardiya_programi_table(conn, existing_tables, is_pg):
    """Anayasa v5.8.5: Vardiya programı tablosunu ve onay kolonlarını garanti eder."""
    _pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    _ts = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if is_pg else "TEXT DEFAULT (datetime('now','localtime'))"
    
    # 1. Tablo Yoksa Oluştur
    if 'personel_vardiya_programi' not in existing_tables:
        sql = f"""CREATE TABLE personel_vardiya_programi (
            id {_pk}, personel_id INTEGER NOT NULL, 
            baslangic_tarihi TEXT NOT NULL, bitis_tarihi TEXT NOT NULL, 
            vardiya TEXT, izin_gunleri TEXT, aciklama TEXT,
            onay_durumu TEXT DEFAULT 'ONAYLANDI', onaylayan_id INTEGER, onay_ts {_ts}
        )"""
        conn.execute(text(sql))
    else:
        # 2. Kolon Kontrolü (Migration)
        cols = ["onay_durumu", "onaylayan_id", "onay_ts"]
        for col in cols:
            try:
                # Kolon var mı kontrol et
                check_sql = f"SELECT {col} FROM personel_vardiya_programi LIMIT 1"
                conn.execute(text(check_sql))
            except:
                # Kolon yoksa ekle
                default_val = "'ONAYLANDI'" if col == "onay_durumu" else "NULL"
                type_val = "TEXT" if col == "onay_durumu" else "INTEGER"
                if col == "onay_ts": type_val = _ts.split(' ')[0]
                
                alter_sql = f"ALTER TABLE personel_vardiya_programi ADD COLUMN {col} {type_val} DEFAULT {default_val}"
                conn.execute(text(alter_sql))

def _create_map_performance_tables(conn, existing_tables, is_pg):
    # MAP tabloları kısaltılmış (Anayasa 30 satır limiti)
    _pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    _ts = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if is_pg else "TEXT DEFAULT (datetime('now','localtime'))"
    if 'map_vardiya' not in existing_tables:
        conn.execute(text(f"CREATE TABLE map_vardiya (id {_pk}, tarih TEXT NOT NULL, makina_no TEXT NOT NULL DEFAULT 'MAP-01', vardiya_no INTEGER NOT NULL, baslangic_saati TEXT NOT NULL, bitis_saati TEXT, operator_adi TEXT NOT NULL, vardiya_sefi TEXT, besleme_kisi INTEGER, kasalama_kisi INTEGER, hedef_hiz_paket_dk FLOAT, gerceklesen_uretim INTEGER DEFAULT 0, acan_kullanici_id INTEGER, kapatan_kullanici_id INTEGER, durum TEXT DEFAULT 'ACIK', notlar TEXT, olusturma_ts {_ts}, guncelleme_ts {_ts})"))
        
    if 'map_zaman_cizelgesi' not in existing_tables:
        conn.execute(text(f"CREATE TABLE map_zaman_cizelgesi (id {_pk}, vardiya_id INTEGER NOT NULL, sira_no INTEGER NOT NULL, baslangic_ts TEXT NOT NULL, bitis_ts TEXT, sure_dk FLOAT, durum TEXT NOT NULL, neden TEXT, aciklama TEXT)"))

    if 'map_fire_kaydi' not in existing_tables:
        conn.execute(text(f"CREATE TABLE map_fire_kaydi (id {_pk}, vardiya_id INTEGER NOT NULL, fire_tipi TEXT NOT NULL, miktar_adet INTEGER NOT NULL, bobin_ref TEXT, aciklama TEXT, olusturma_ts {_ts})"))

    if 'map_bobin_kaydi' not in existing_tables:
        conn.execute(text(f"CREATE TABLE map_bobin_kaydi (id {_pk}, vardiya_id INTEGER NOT NULL, sira_no INTEGER NOT NULL, degisim_ts TEXT NOT NULL, bobin_lot TEXT NOT NULL, film_tipi TEXT DEFAULT 'Üst Film', baslangic_kg FLOAT, bitis_kg FLOAT, kullanilan_kg FLOAT, aciklama TEXT)"))

def _create_performans_tables(conn, existing_tables, is_pg):
    """v5.8.15: Performans & Polivalans tablolarını otomatik oluşturur (Cloud+Local)."""
    _pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    _ts = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if is_pg else "TEXT DEFAULT (datetime('now','localtime'))"
    if 'performans_degerledirme' not in existing_tables:
        conn.execute(text(f"""
            CREATE TABLE performans_degerledirme (
                id {_pk}, uuid TEXT UNIQUE NOT NULL,
                personel_id INTEGER, calisan_adi_soyadi TEXT NOT NULL,
                bolum TEXT NOT NULL, gorevi TEXT NOT NULL, ise_giris_tarihi DATE,
                donem TEXT NOT NULL, degerlendirme_tarihi DATE NOT NULL,
                degerlendirme_yili INTEGER NOT NULL,
                kkd_kullanimi INTEGER, mesleki_kriter_2 INTEGER, mesleki_kriter_3 INTEGER,
                mesleki_kriter_4 INTEGER, mesleki_kriter_5 INTEGER, mesleki_kriter_6 INTEGER,
                mesleki_kriter_7 INTEGER, mesleki_kriter_8 INTEGER,
                mesleki_ortalama_puan REAL,
                calisma_saatleri_uyum INTEGER, ogrenme_kabiliyeti INTEGER,
                iletisim_becerisi INTEGER, problem_cozme INTEGER, kalite_bilinci INTEGER,
                ise_baglilik_aidiyet INTEGER, ekip_calismasi_uyum INTEGER, verimli_calisma INTEGER,
                kurumsal_ortalama_puan REAL, agirlikli_toplam_puan REAL NOT NULL,
                polivalans_duzeyi TEXT NOT NULL, polivalans_kodu INTEGER NOT NULL,
                yorum TEXT, degerlendiren_adi TEXT,
                olusturma_tarihi {_ts}, guncelleyen_kullanici TEXT,
                surum INTEGER DEFAULT 1, onceki_puan REAL,
                sync_durumu TEXT DEFAULT 'bekliyor', silinmis INTEGER DEFAULT 0
            )
        """))
    if 'polivalans_matris' not in existing_tables:
        conn.execute(text(f"""
            CREATE TABLE polivalans_matris (
                id {_pk}, personel_id INTEGER, calisan_adi TEXT NOT NULL,
                bolum TEXT NOT NULL, gorevi TEXT NOT NULL, guncelleme_yili INTEGER NOT NULL,
                son_puan_d1 REAL, son_puan_d2 REAL, yil_ortalama REAL,
                polivalans_kodu INTEGER, polivalans_metni TEXT,
                puan_degisimi REAL, egitim_ihtiyaci INTEGER DEFAULT 0,
                olusturma_tarihi {_ts}, sync_durumu TEXT DEFAULT 'bekliyor'
            )
        """))

def _cleanup_old_logs(conn, is_pg):
    """v4.0.6: 90 günden eski logları sistemden temizler."""
    try:
        if is_pg:
            stmt = "DELETE FROM sistem_loglari WHERE zaman < CURRENT_TIMESTAMP - INTERVAL '90 days'"
        else:
            stmt = "DELETE FROM sistem_loglari WHERE zaman < datetime('now', '-90 days')"
        conn.execute(text(stmt))
    except Exception as e:
        print(f"Log Cleanup Warning: {e}")

def _bootstrap_modules(conn, is_pg):
    """Anayasa v4.0.7: Modül listesini atomik, zorlayıcı ve ZONE (Bölge) destekli senkronize eder."""
    try:
        # v5.4.0: Modül Anahtarı, Etiket, Sıra, Varsayılan Zone (ops, mgt, sys)
        MODUL_LISTESI = [
            ("uretim_girisi", "🏭 Üretim Girişi", 10, "ops"),
            ("kpi_kontrol", "🍩 KPI & Kalite Kontrol", 20, "ops"),
            ("gmp_denetimi", "🛡️ GMP Denetimi", 30, "ops"),
            ("personel_hijyen", "🧼 Personel Hijyen", 40, "ops"),
            ("temizlik_kontrol", "🧹 Temizlik Kontrol", 50, "ops"),
            ("kurumsal_raporlama", "📊 Kurumsal Raporlama", 60, "mgt"),
            ("soguk_oda", "❄️ Soğuk Oda Sıcaklıkları", 70, "ops"),
            ("map_uretim", "📦 MAP Üretim", 80, "ops"),
            ("gunluk_gorevler", "📋 Günlük Görevler", 85, "ops"),
            ("performans_polivalans", "📈 Yetkinlik & Performans", 90, "mgt"),
            ("personel_vardiya_yonetimi", "📅 Vardiya Yönetimi", 95, "ops"),
            ("qdms", "📁 QDMS", 100, "mgt"),
            ("ayarlar", "⚙️ Ayarlar", 110, "sys")
        ]
        
        for anahtar, etiket, sira, zone in MODUL_LISTESI:
            if is_pg:
                stmt = text("""
                    INSERT INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, zone, aktif)
                    VALUES (:k, :e, :s, :z, 1)
                    ON CONFLICT (modul_anahtari) DO UPDATE SET 
                        modul_etiketi = EXCLUDED.modul_etiketi,
                        sira_no = EXCLUDED.sira_no,
                        zone = COALESCE(ayarlar_moduller.zone, EXCLUDED.zone),
                        aktif = 1
                """)
            else:
                # SQLite: Mevcut zone NULL ise yeni zone'u bas, değilse koru.
                stmt = text("""
                    INSERT INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, zone, aktif)
                    VALUES (:k, :e, :s, :z, 1)
                    ON CONFLICT (modul_anahtari) DO UPDATE SET 
                        modul_etiketi = EXCLUDED.modul_etiketi,
                        sira_no = EXCLUDED.sira_no,
                        zone = CASE WHEN ayarlar_moduller.zone IS NULL THEN EXCLUDED.zone ELSE ayarlar_moduller.zone END,
                        aktif = 1
                """)
            conn.execute(stmt, {"k": anahtar, "e": etiket, "s": sira, "z": zone})
            
    except Exception as e:
        print(f"Bootstrap v5.4.0 Warning: {e}")

def _bootstrap_performans_yetkiler(conn, is_pg):
    """v5.9.0: performans_polivalans için yetki girişi yoksa mgt-zone rollerinden türetir.
    Sıfır Hardcode: Hangi rollerin erişeceği DB'deki mevcut yetkilerden çıkarılır.
    """
    try:
        # mgt zone'undaki başka bir modüle (örn. kpi_kontrol) erişimi olan
        # rolleri bul, eğer henüz performans_polivalans'ları yoksa ekle
        if is_pg:
            stmt = text("""
                INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu)
                SELECT DISTINCT y.rol_adi, 'performans_polivalans', y.erisim_turu
                FROM ayarlar_yetkiler y
                JOIN ayarlar_moduller m ON m.modul_anahtari = y.modul_adi
                WHERE m.zone = 'mgt'
                  AND y.erisim_turu NOT IN ('Yok', '')
                  AND y.erisim_turu IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM ayarlar_yetkiler
                      WHERE rol_adi = y.rol_adi AND modul_adi = 'performans_polivalans'
                  )
            """)
        else:
            stmt = text("""
                INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu)
                SELECT DISTINCT y.rol_adi, 'performans_polivalans', y.erisim_turu
                FROM ayarlar_yetkiler y
                JOIN ayarlar_moduller m ON m.modul_anahtari = y.modul_adi
                WHERE m.zone = 'mgt'
                  AND y.erisim_turu NOT IN ('Yok', '')
                  AND y.erisim_turu IS NOT NULL
                  AND NOT EXISTS (
                      SELECT 1 FROM ayarlar_yetkiler
                      WHERE rol_adi = y.rol_adi AND modul_adi = 'performans_polivalans'
                  )
            """)
        conn.execute(stmt)
    except Exception as e:
        print(f"Bootstrap Performans Yetkiler Warning: {e}")

def _ensure_admin_account_with_conn(conn, is_pg):
    """Sistem hesaplarını (Admin & Saha_Mobil) garanti eder."""
    try:
        table_path = "public.personel" if is_pg else "personel"
        # 1. Admin Hesabı
        res_admin = conn.execute(text(f"SELECT COUNT(*) FROM {table_path} WHERE kullanici_adi = 'Admin'")).fetchone()
        if res_admin[0] == 0:
            conn.execute(text(f"""
                INSERT INTO {table_path} (ad_soyad, kullanici_adi, sifre, rol, durum, pozisyon_seviye)
                VALUES ('SİSTEM ADMİN', 'Admin', '12345', 'ADMIN', 'AKTİF', 0)
            """))
            
        # 2. Saha_Mobil Hesabı (Mobil Girişler İçin)
        res_mobil = conn.execute(text(f"SELECT COUNT(*) FROM {table_path} WHERE kullanici_adi = 'Saha_Mobil'")).fetchone()
        if res_mobil[0] == 0:
            conn.execute(text(f"""
                INSERT INTO {table_path} (ad_soyad, kullanici_adi, sifre, rol, durum, pozisyon_seviye)
                VALUES ('SAHA MOBİL TERMİNAL', 'Saha_Mobil', 'mobil789', 'Personel', 'AKTİF', 5)
            """))
    except Exception as e:
        print(f"System Account Ensure Error: {e}")

def _run_naming_migration_with_conn(conn, is_pg):
    """v4.1.4: Modül isimlerini merkezi olarak standardize eder (EKL-NAMING-001)."""
    try:
        OLD_L = "📊 Performans & Polivalans"
        NEW_L = "📈 Yetkinlik & Performans"
        
        # 1. ayarlar_moduller (UI'da görünen etiketler)
        conn.execute(text("""
            UPDATE ayarlar_moduller 
            SET modul_etiketi = :nl 
            WHERE modul_etiketi = :ol OR modul_anahtari = 'performans_polivalans'
        """), {"nl": NEW_L, "ol": OLD_L})
        
        # 2. sistem_modulleri (Varsa eski yapı)
        try:
            conn.execute(text("""
                UPDATE sistem_modulleri 
                SET etiket = :nl 
                WHERE etiket = :ol OR anahtar = 'performans_polivalans'
            """), {"nl": NEW_L, "ol": OLD_L})
        except: pass
    except Exception as e:
        print(f"Naming Migration Warning: {e}")

def _bootstrap_qms_departments(conn, is_pg):
    """QMS Departman yapısı için başlangıç verilerini ve türleri eklendiğini garanti eder."""
    try:
        # 1. Türleri Ekle (20 Seviye Desteği)
        turler = [
            ('GENEL MÜDÜRLÜK', 1), ('DİREKTÖRLÜK', 2), ('DEPARTMAN', 3), 
            ('BRİM', 4), ('ALAN / HAT', 5), ('İSTASYON', 6), ('MAKİNE', 7),
            ('ALT-BİRİM 8', 8), ('ALT-BİRİM 9', 9), ('ALT-BİRİM 10', 10),
            ('ALT-BİRİM 11', 11), ('ALT-BİRİM 12', 12), ('ALT-BİRİM 13', 13),
            ('ALT-BİRİM 14', 14), ('ALT-BİRİM 15', 15), ('ALT-BİRİM 16', 16),
            ('ALT-BİRİM 17', 17), ('ALT-BİRİM 18', 18), ('ALT-BİRİM 19', 19), ('ALT-BİRİM 20', 20)
        ]
        for ad, sira in turler:
            sql = "INSERT INTO qms_departman_turleri (tur_adi, sira_no) VALUES (:a, :s)"
            if is_pg: sql += " ON CONFLICT (tur_adi) DO NOTHING"
            else: sql = sql.replace("INSERT INTO", "INSERT OR IGNORE INTO")
            conn.execute(text(sql), {"a": ad, "s": sira})

        # 2. Temel Departmanları Ekle (Eğer tablo boşsa)
        res = conn.execute(text("SELECT COUNT(*) FROM qms_departmanlar")).fetchone()
        if res[0] == 0:
            # v6.3: Tam Hiyerarşi Seeding (media__1775039977091.png uyarınca)
            # (Ad, Ust_Ad, Tur_ID)
            tree = [
                ('GENEL MÜDÜRLÜK', None, 1),
                ('ÜRETİM', 'GENEL MÜDÜRLÜK', 3),
                ('İNSAN KAYNAKLARI', 'GENEL MÜDÜRLÜK', 3),
                ('KALİTE', 'GENEL MÜDÜRLÜK', 3),
                ('MUHASEBE', 'GENEL MÜDÜRLÜK', 3),
                ('SEVKİYAT', 'GENEL MÜDÜRLÜK', 3),
                ('PLANLAMA', 'GENEL MÜDÜRLÜK', 3),
                
                # Üretim Altı
                ('YARI MAMÜL', 'ÜRETİM', 4),
                ('EKLER', 'ÜRETİM', 4),
                ('HACI NADİR', 'ÜRETİM', 4),
                ('OKUL', 'ÜRETİM', 4),
                ('TEMİZLİK (Üretim)', 'ÜRETİM', 4),
                
                # Yarı Mamül Altı
                ('KREMA', 'YARI MAMÜL', 5), ('PANDİSPANYA', 'YARI MAMÜL', 5), ('PATAŞU', 'YARI MAMÜL', 5),
                
                # Ekler Altı
                ('MEYVE', 'EKLER', 5), ('DOLUM', 'EKLER', 5), ('SOS', 'EKLER', 5), ('KREMA ', 'EKLER', 5),
                ('DEKOR', 'EKLER', 5), ('MAP', 'EKLER', 5), ('TERAZİ', 'EKLER', 5), ('MAGNOLYA', 'EKLER', 5),
                
                # Hacı Nadir Altı
                ('TEK PASTA', 'HACI NADİR', 5), ('KURU PASTA', 'HACI NADİR', 5), ('PASTA', 'HACI NADİR', 5), ('BAKLAVA', 'HACI NADİR', 5),
                
                # Okul Altı
                ('PROFİTEROL', 'OKUL', 5), ('BOMBA', 'OKUL', 5), ('RULO PASTA', 'OKUL', 5),
                
                # Temizlik Altı
                ('BULAŞIKHANE', 'TEMİZLİK (Üretim)', 5), ('TEMİZLİK ', 'TEMİZLİK (Üretim)', 5),
                
                # Diğerleri
                ('İŞ GÜVENLİĞİ', 'KALİTE', 4),
                ('YARI MAMÜL DEPO', 'PLANLAMA', 4), ('MAMÜL DEPO', 'PLANLAMA', 4), ('HAM MADDE DEPO', 'PLANLAMA', 4)
            ]
            
            # ID Mapping Sözlüğü
            id_map = {}
            for ad, parent_ad, tur_id in tree:
                parent_id = id_map.get(parent_ad) if parent_ad else None
                res_ins = conn.execute(text("INSERT INTO qms_departmanlar (ad, ust_id, tur_id) VALUES (:a, :p, :t) RETURNING id"), {"a": ad, "p": parent_id, "t": tur_id})
                new_id = res_ins.fetchone()[0]
                id_map[ad] = new_id
            
            # v6.1: Personel mapping sync denemesi
            conn.execute(text("UPDATE personel SET qms_departman_id = (SELECT id FROM qms_departmanlar WHERE ad = 'ÜRETİM' LIMIT 1) WHERE qms_departman_id IS NULL"))

    except Exception as e:
        print(f"Bootstrap QMS Departments Warning: {e}")

# Global engine nesnesi (Anayasa v3.3: MODÜL DÜZEYİNDE ÇAĞRI KALDIRILDI)
# Artık her modül kendi içinde get_engine() çağırmalıdır. (Lazy Loading)
# engine = get_engine()  <-- DELETED to prevent ImportError cascade
