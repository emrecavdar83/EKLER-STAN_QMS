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
    # SQLite fallback
    cols = []
    for t in ['urun_kpi_kontrol', 'sicaklik_olcumleri', 'ayarlar_roller', 'personel']:
        try:
            c_res = conn.execute(text(f"PRAGMA table_info({t})")).fetchall()
            for c in c_res: cols.append((t, c[1]))
        except: pass
    return cols

def _get_migration_list():
    return [
        ("urun_kpi_kontrol", "fotograf_b64", "ALTER TABLE urun_kpi_kontrol ADD COLUMN fotograf_b64 TEXT"),
        ("sicaklik_olcumleri", "planlanan_zaman", "ALTER TABLE sicaklik_olcumleri ADD COLUMN planlanan_zaman TIMESTAMP"),
        ("sicaklik_olcumleri", "qr_ile_girildi", "ALTER TABLE sicaklik_olcumleri ADD COLUMN qr_ile_girildi INTEGER DEFAULT 1"),
        ("ayarlar_roller", "aktif", "ALTER TABLE ayarlar_roller ADD COLUMN aktif INTEGER DEFAULT 1"),
        ("personel", "guncelleme_tarihi", "ALTER TABLE personel ADD COLUMN guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    ]



def _ensure_critical_data_with_conn(conn, is_pg):
    """Sabit verileri ve hayalet tabloları garanti eder."""
    res_tabs = _get_existing_tables(conn, is_pg)
    existing_tables = {r[0].lower() for r in res_tabs}
    
    _create_shadow_tables(conn, existing_tables, is_pg)
    _create_map_performance_tables(conn, existing_tables, is_pg)
    _bootstrap_modules(conn, is_pg)

def _get_existing_tables(conn, is_pg):
    if is_pg:
        return conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
    return conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()

def _create_shadow_tables(conn, existing_tables, is_pg):
    _pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
    shadow_tabs = [
        ('sistem_loglari', f"CREATE TABLE sistem_loglari (id {_pk}, islem_tipi VARCHAR(50), detay TEXT, zaman TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"),
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
        conn.execute(text(f"CREATE TABLE map_vardiya (id {_pk}, tarih TEXT NOT NULL, makina_no TEXT NOT NULL DEFAULT 'MAP-01', vardiya_no INTEGER NOT NULL, baslangic_saati TEXT NOT NULL, bitis_saati TEXT, operator_adi TEXT NOT NULL, acan_kullanici_id INTEGER, kapatan_kullanici_id INTEGER, durum TEXT DEFAULT 'ACIK', olusturma_ts {_ts}, guncelleme_ts {_ts})"))

def _bootstrap_modules(conn, is_pg):
    """Anayasa v3.2: Modül listesini atomik ve zorlayıcı bir şekilde senkronize eder."""
    try:
        # Orijinal sıralamayı korumak için MODUL_LISTESI
        MODUL_LISTESI = [
            ("Üretim Girişi", "🏭 Üretim Girişi", 10),
            ("KPI Kontrol", "🍩 KPI & Kalite Kontrol", 20),
            ("GMP Denetimi", "🛡️ GMP Denetimi", 30),
            ("Personel Hijyen", "🧼 Personel Hijyen", 40),
            ("Temizlik Kontrol", "🧹 Temizlik Kontrol", 50),
            ("Raporlama", "📊 Kurumsal Raporlama", 60),
            ("Soğuk Oda", "❄️ Soğuk Oda Sıcaklıkları", 70),
            ("MAP Üretim", "📦 MAP Üretim", 80),
            ("Performans & Polivalans", "📊 Performans & Polivalans", 90),
            ("qdms", "📁 QDMS", 100),
            ("Ayarlar", "⚙️ Ayarlar", 110)
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
    """Admin kullanıcısı yoksa oluşturur."""
    try:
        res = conn.execute(text("SELECT COUNT(*) FROM public.personel WHERE kullanici_adi = 'Admin'")).fetchone()
        if res[0] == 0:
            conn.execute(text("""
                INSERT INTO public.personel (ad_soyad, kullanici_adi, sifre, rol, durum, pozisyon_seviye)
                VALUES ('SİSTEM ADMİN', 'Admin', '12345', 'ADMIN', 'AKTİF', 0)
            """))
    except Exception as e:
        print(f"Admin Ensure Error: {e}")

# Global engine nesnesi (Geriye uyumluluk için, artık lazy)
engine = get_engine()

# Eski fonksiyonlar kaldırıldı (Operation Flash Adım 3)
