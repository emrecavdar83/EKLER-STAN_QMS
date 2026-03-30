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
            _ensure_schema_sync_with_conn(conn, is_pg)
            _ensure_critical_data_with_conn(conn, is_pg)
            _ensure_admin_account_with_conn(conn, is_pg)
            
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
        print(f"Maintenance partially completed with error: {e}")
        st.warning(f"⚠️ Sistem bakımı kısmi tamamlandı: {e}")
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
        ("sistem_loglari", "cihaz_bilgisi", "ALTER TABLE sistem_loglari ADD COLUMN cihaz_bilgisi TEXT")
    ]



def _ensure_critical_data_with_conn(conn, is_pg):
    """Sabit verileri ve hayalet tabloları garanti eder."""
    res_tabs = _get_existing_tables(conn, is_pg)
    existing_tables = {r[0].lower() for r in res_tabs}
    
    _create_shadow_tables(conn, existing_tables, is_pg)
    _cleanup_old_logs(conn, is_pg)
    _create_map_performance_tables(conn, existing_tables, is_pg)
    _bootstrap_modules(conn, is_pg)

def _get_existing_tables(conn, is_pg):
    if is_pg:
        return conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
    return conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()

def _create_shadow_tables(conn, existing_tables, is_pg):
    _pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    _ts = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if is_pg else "TEXT DEFAULT (datetime('now','localtime'))"
    shadow_tabs = [
        ('sistem_loglari', f"CREATE TABLE sistem_loglari (id {_pk}, islem_tipi VARCHAR(50), detay TEXT, modul VARCHAR(50), kullanici_id INTEGER, detay_json TEXT, ip_adresi VARCHAR(45), cihaz_bilgisi TEXT, zaman TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"),
        ('hata_loglari', f"CREATE TABLE hata_loglari (id {_pk}, hata_kodu VARCHAR(20) UNIQUE NOT NULL, seviye VARCHAR(20) DEFAULT 'ERROR', modul VARCHAR(50), fonksiyon VARCHAR(100), hata_mesaji TEXT NOT NULL, stack_trace TEXT, context_data TEXT, ai_diagnosis TEXT, kullanici_id INTEGER, is_fixed INTEGER DEFAULT 0, zaman {_ts})"),
        ('lokasyon_tipleri', f"CREATE TABLE lokasyon_tipleri (id {_pk}, tip_adi VARCHAR(50) UNIQUE NOT NULL, sira_no INTEGER DEFAULT 10, aktif INTEGER DEFAULT 1)"),
        ('vardiya_tipleri', f"CREATE TABLE vardiya_tipleri (id {_pk}, tip_adi VARCHAR(50) UNIQUE NOT NULL, sira_no INTEGER DEFAULT 10, aktif INTEGER DEFAULT 1)")
    ]
    for t_name, t_sql in shadow_tabs:
        if t_name not in existing_tables:
            try:
                # PG için bağlantı zaten AUTOCOMMIT modunda (üst fonksiyondan geliyor)
                conn.execute(text(t_sql))
            except Exception as e:
                print(f"Shadow Table Error ({t_name}): {e}")

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
    """Anayasa v3.2: Modül listesini atomik ve zorlayıcı bir şekilde senkronize eder."""
    try:
        # Orijinal sıralamayı korumak için MODUL_LISTESI
        MODUL_LISTESI = [
            ("uretim_girisi", "🏭 Üretim Girişi", 10),
            ("kpi_kontrol", "🍩 KPI & Kalite Kontrol", 20),
            ("gmp_denetimi", "🛡️ GMP Denetimi", 30),
            ("personel_hijyen", "🧼 Personel Hijyen", 40),
            ("temizlik_kontrol", "🧹 Temizlik Kontrol", 50),
            ("kurumsal_raporlama", "📊 Kurumsal Raporlama", 60),
            ("soguk_oda", "❄️ Soğuk Oda Sıcaklıkları", 70),
            ("map_uretim", "📦 MAP Üretim", 80),
            ("gunluk_gorevler", "📋 Günlük Görevler", 85),
            ("performans_polivalans", "📈 Yetkinlik & Performans", 90),
            ("qdms", "📁 QDMS", 100),
            ("ayarlar", "⚙️ Ayarlar", 110)
        ]
        
        # Optimized Bulk Insert (EKL-PERF-001) - 1 Round-Trip
        placeholders = []
        params = {}
        for i, (anahtar, etiket, sira) in enumerate(MODUL_LISTESI):
            placeholders.append(f"(:k{i}, :e{i}, :s{i}, 1)")
            params[f"k{i}"] = anahtar
            params[f"e{i}"] = etiket
            params[f"s{i}"] = sira
            
        multi_values = ", ".join(placeholders)
        
        if is_pg:
            stmt = f"""
                INSERT INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, aktif)
                VALUES {multi_values}
                ON CONFLICT (modul_anahtari) DO UPDATE SET 
                    modul_etiketi = EXCLUDED.modul_etiketi,
                    sira_no = EXCLUDED.sira_no,
                    aktif = 1
            """
        else:
            stmt = f"""
                INSERT OR REPLACE INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, aktif)
                VALUES {multi_values}
            """
        conn.execute(text(stmt), params)
    except Exception as e:
        print(f"Bootstrap Warning: {e}")

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

# Global engine nesnesi (Anayasa v3.3: MODÜL DÜZEYİNDE ÇAĞRI KALDIRILDI)
# Artık her modül kendi içinde get_engine() çağırmalıdır. (Lazy Loading)
# engine = get_engine()  <-- DELETED to prevent ImportError cascade
