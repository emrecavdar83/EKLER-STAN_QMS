import streamlit as st
from sqlalchemy import create_engine, text

@st.cache_resource
def init_connection():
    """Veritabanı bağlantı motorunu (engine) oluşturur ve önbelleğe alır."""
    # Streamlit Cloud Secret kontrolü (Hiyerarşik kontrol: root -> streamlit -> fallback)
    db_url = None
    if "DB_URL" in st.secrets:
        db_url = st.secrets["DB_URL"]
    elif "streamlit" in st.secrets and "DB_URL" in st.secrets["streamlit"]:
        db_url = st.secrets["streamlit"]["DB_URL"]
    
    if db_url:
        engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True, 
            pool_recycle=300
        )
        
        # 13. ADAM PROTOKOLÜ: PostgreSQL Zaman Dilimi Senkronizasyonu
        if 'postgresql' in db_url:
            from sqlalchemy import event
            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("SET TIMEZONE='Europe/Istanbul'")
                cursor.close()
        
        return engine
    else:
        # Lokal Fallback
        db_url = 'sqlite:///ekleristan_local.db'
        engine = create_engine(db_url, connect_args={'check_same_thread': False})
        
        # 13. ADAM PROTOKOLÜ: SQLite WAL Modu (Concurrency Zırhı)
        from sqlalchemy import event
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.close()
            
        return engine

def auto_migrate_schema(eng):
    """Bulut ve yerelde eksik olabilecek kritik sütunları otomatik ekler."""
    migrations = [
        "ALTER TABLE urun_kpi_kontrol ADD COLUMN fotograf_b64 TEXT",
        "ALTER TABLE sicaklik_olcumleri ADD COLUMN planlanan_zaman TIMESTAMP",
        "ALTER TABLE sicaklik_olcumleri ADD COLUMN qr_ile_girildi INTEGER DEFAULT 1",
        "ALTER TABLE ayarlar_roller ADD COLUMN aktif INTEGER DEFAULT 1",
        "ALTER TABLE personel ADD COLUMN guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        "ALTER TABLE ayarlar_bolumler ADD COLUMN guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
    ]
    
    # PostgreSQL'de transaction poison (InFailedSqlTransaction) olmasını engellemek için AUTOCOMMIT
    is_pg = eng.dialect.name == 'postgresql'
    conn_pool = eng.connect().execution_options(isolation_level="AUTOCOMMIT") if is_pg else eng.connect()
    
    with conn_pool as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
            except Exception:
                pass
                
        # 0. SİSTEM LOGLARI (Audit Log Zırhı)
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS sistem_loglari (
                id """ + ("INTEGER PRIMARY KEY AUTOINCREMENT" if not is_pg else "SERIAL PRIMARY KEY") + """,
                islem_tipi VARCHAR(50),
                detay TEXT,
                zaman TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """))
        except Exception:
            pass

        # 13. ADAM SIFIR RİSK PROTOKOLÜ: Lokasyon Tipleri Hayalet Tablosu
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS lokasyon_tipleri (
                id """ + ("INTEGER PRIMARY KEY AUTOINCREMENT" if not is_pg else "SERIAL PRIMARY KEY") + """,
                tip_adi VARCHAR(50) UNIQUE NOT NULL,
                sira_no INTEGER DEFAULT 10,
                aktif INTEGER DEFAULT 1
            )
            """))
            # Varsayılanları enjekte et
            for t_adi, t_sira in [('Kat', 1), ('Bölüm', 2), ('Hat', 3), ('Ekipman', 4)]:
                try:
                    conn.execute(text("INSERT INTO lokasyon_tipleri (tip_adi, sira_no) VALUES (:t, :s)"), {"t": t_adi, "s": t_sira})
                except Exception:
                    pass
        except Exception as e:
            print(f"Hayalet tablo hatası: {e}")

        # 13. ADAM SIFIR RİSK PROTOKOLÜ: Vardiya Tipleri Hayalet Tablosu (Madde 1)
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS vardiya_tipleri (
                id """ + ("INTEGER PRIMARY KEY AUTOINCREMENT" if not is_pg else "SERIAL PRIMARY KEY") + """,
                tip_adi VARCHAR(50) UNIQUE NOT NULL,
                sira_no INTEGER DEFAULT 10,
                aktif INTEGER DEFAULT 1
            )
            """))
            for t_adi, t_sira in [('GÜNDÜZ VARDİYASI', 1), ('ARA VARDİYA', 2), ('GECE VARDİYASI', 3)]:
                try:
                    conn.execute(text("INSERT INTO vardiya_tipleri (tip_adi, sira_no) VALUES (:t, :s)"), {"t": t_adi, "s": t_sira})
                except Exception:
                    pass
        except Exception as e:
            print(f"Vardiya tipleri shadow hatası: {e}")

        # 13. ADAM SIFIR RİSK PROTOKOLÜ: İzin Günleri Hayalet Tablosu (Madde 1)
        try:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS izin_gunleri_tipleri (
                id """ + ("INTEGER PRIMARY KEY AUTOINCREMENT" if not is_pg else "SERIAL PRIMARY KEY") + """,
                tip_adi VARCHAR(50) UNIQUE NOT NULL,
                sira_no INTEGER DEFAULT 10,
                aktif INTEGER DEFAULT 1
            )
            """))
            for t_adi, t_sira in [('Pazar', 1), ('Cumartesi,Pazar', 2), ('Cumartesi', 3), ('Pazartesi', 4), ('Salı', 5), ('Çarşamba', 6), ('Perşembe', 7), ('Cuma', 8)]:
                try:
                    conn.execute(text("INSERT INTO izin_gunleri_tipleri (tip_adi, sira_no) VALUES (:t, :s)"), {"t": t_adi, "s": t_sira})
                except Exception:
                    pass
        except Exception as e:
            print(f"İzin günleri shadow hatası: {e}")

        # 13. ADAM SIFIR RİSK PROTOKOLÜ: AKILLI AKIŞ VE GÖREV MOTORU ŞEMASI
        smart_flow_tables = [
            # 1. Akış Tanımları (Flow Engine)
            """CREATE TABLE IF NOT EXISTS flow_definitions (
                id AUTO_ID_PLACEHOLDER,
                flow_name VARCHAR(100) UNIQUE NOT NULL,
                urun_grubu VARCHAR(100), -- Ekler, Bomba vb.
                aktif INTEGER DEFAULT 1,
                olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            # 2. Akış Düğümleri (Nodes)
            """CREATE TABLE IF NOT EXISTS flow_nodes (
                id AUTO_ID_PLACEHOLDER,
                flow_id INTEGER NOT NULL,
                node_name VARCHAR(100) NOT NULL,
                node_type VARCHAR(50) DEFAULT 'PROSES', -- GİRİŞ, PROSES, ÖLÇÜM, KARAR, ÇIKIŞ
                lokasyon_id INTEGER, -- Hangi ekipman/bölümde?
                sira_no INTEGER DEFAULT 10,
                kural_set_json TEXT, -- n8n mantığı için kural tanımları
                aktif INTEGER DEFAULT 1
            )""",
            # 3. Akış Bağlantıları (Edges)
            """CREATE TABLE IF NOT EXISTS flow_edges (
                id AUTO_ID_PLACEHOLDER,
                flow_id INTEGER NOT NULL,
                source_node_id INTEGER NOT NULL,
                target_node_id INTEGER NOT NULL,
                condition_rule TEXT -- Dallanma (Ekler sağa, Bomba sola)
            )""",
            # 4. Görev Atama Motoru (Task Management)
            """CREATE TABLE IF NOT EXISTS personnel_tasks (
                id AUTO_ID_PLACEHOLDER,
                node_id INTEGER NOT NULL,
                personel_id INTEGER NOT NULL,
                batch_id VARCHAR(100), -- Hangi parti için?
                durum VARCHAR(50) DEFAULT 'BEKLIYOR', -- BEKLIYOR, AKTIF, TAMAMLANDI, BYPASS
                atanma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tamamlanma_zamani TIMESTAMP
            )""",
            # 5. 13. Adam / Eğitim Modu Bypass Logları
            """CREATE TABLE IF NOT EXISTS flow_bypass_logs (
                id AUTO_ID_PLACEHOLDER,
                node_id INTEGER NOT NULL,
                personel_id INTEGER NOT NULL,
                sebep TEXT,
                zaman_damgasi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                enforcement_level VARCHAR(20) DEFAULT 'SOFT'
            )"""
        ]

        for table_sql in smart_flow_tables:
            try:
                # SQLite/PostgreSQL uyumlu ID tipi ayarı
                id_type = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
                final_sql = table_sql.replace("AUTO_ID_PLACEHOLDER", id_type)
                conn.execute(text(final_sql))
            except Exception as e:
                print(f"Smart Flow Tablo Hatası: {e}")

        # PostgreSQL Sequence Senkronizasyonu
        if is_pg:
            tables_to_sync = [
                'hijyen_kontrol_kayitlari', 'depo_giris_kayitlari', 'urun_kpi_kontrol', 
                'sicaklik_olcumleri', 'olcum_plani', 'temizlik_kayitlari', 'personel'
            ]
            for tbl in tables_to_sync:
                try:
                    sync_sql = text(f"SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), COALESCE((SELECT MAX(id) FROM {tbl}), 1), true)")
                    conn.execute(sync_sql)
                except Exception:
                    try:
                        sync_sql_fb = text(f"SELECT setval('{tbl}_id_seq', COALESCE((SELECT MAX(id) FROM {tbl}), 1), true)")
                        conn.execute(sync_sql_fb)
                    except Exception:
                        pass
        
        # MAP ÜRETIM TAKİP MODÜLÜ — 4 TABLO (13. Adam: CREATE IF NOT EXISTS, side-effect-free)
        _pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
        _ts = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if is_pg else "TEXT DEFAULT (datetime('now','localtime'))"
        map_tablolari = [
            f"""CREATE TABLE IF NOT EXISTS map_vardiya (
                id {_pk}, tarih TEXT NOT NULL, makina_no TEXT NOT NULL DEFAULT 'MAP-01',
                vardiya_no INTEGER NOT NULL, baslangic_saati TEXT NOT NULL, bitis_saati TEXT,
                operator_adi TEXT NOT NULL, vardiya_sefi TEXT, besleme_kisi INTEGER DEFAULT 0,
                kasalama_kisi INTEGER DEFAULT 0, hedef_hiz_paket_dk REAL DEFAULT 4.2,
                gerceklesen_uretim INTEGER DEFAULT 0, durum TEXT DEFAULT 'ACIK', notlar TEXT,
                olusturma_ts {_ts}, guncelleme_ts {_ts}
            )""",
            f"""CREATE TABLE IF NOT EXISTS map_zaman_cizelgesi (
                id {_pk}, vardiya_id INTEGER NOT NULL REFERENCES map_vardiya(id),
                sira_no INTEGER NOT NULL, baslangic_ts TEXT NOT NULL, bitis_ts TEXT,
                sure_dk REAL, durum TEXT NOT NULL, neden TEXT, aciklama TEXT,
                olusturma_ts {_ts}
            )""",
            f"""CREATE TABLE IF NOT EXISTS map_bobin_kaydi (
                id {_pk}, vardiya_id INTEGER NOT NULL REFERENCES map_vardiya(id),
                sira_no INTEGER NOT NULL, degisim_ts TEXT NOT NULL, bobin_lot TEXT,
                baslangic_m REAL DEFAULT 300, bitis_m REAL, kullanilan_m REAL, aciklama TEXT,
                olusturma_ts {_ts}
            )""",
            f"""CREATE TABLE IF NOT EXISTS map_fire_kaydi (
                id {_pk}, vardiya_id INTEGER NOT NULL REFERENCES map_vardiya(id),
                fire_tipi TEXT NOT NULL, miktar_adet INTEGER NOT NULL DEFAULT 0,
                bobin_ref TEXT, aciklama TEXT, olusturma_ts {_ts}
            )""",
        ]
        for tbl_sql in map_tablolari:
            try:
                conn.execute(text(tbl_sql))
            except Exception as e:
                print(f"MAP Tablo Hatası: {e}")

        # MAP Üretim modülünü ayarlar_moduller'e garantile (session'dan bağımsız)
        try:
            _map_etiket = "📦 MAP Üretim"
            _map_anahtar = "MAP Üretim"
            if is_pg:
                conn.execute(text("""
                    INSERT INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, aktif)
                    VALUES (:k, :e, 90, 1)
                    ON CONFLICT (modul_anahtari) DO NOTHING
                """), {"k": _map_anahtar, "e": _map_etiket})
            else:
                conn.execute(text("""
                    INSERT OR IGNORE INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, aktif)
                    VALUES (:k, :e, 90, 1)
                """), {"k": _map_anahtar, "e": _map_etiket})
        except Exception as e:
            print(f"MAP Bootstrap Hatası: {e}")

        if not is_pg:
            conn.commit()


# Global engine nesnesi
engine = init_connection()
try:
    auto_migrate_schema(engine)
except Exception:
    pass  # Başlangıç migrasyonu başarısız olsa bile uygulama açılmaya devam eder

def get_engine():
    """Uygulama genelinde kullanılacak engine nesnesini döndürür."""
    return engine

def guvenli_admin_olustur():
    """Admin kullanıcısı yoksa oluşturur (Canlı ve Yerel ortamda ortak)"""
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT COUNT(*) FROM personel WHERE kullanici_adi = 'Admin'")).fetchone()
            if res[0] == 0:
                conn.execute(text("""
                    INSERT INTO personel (ad_soyad, kullanici_adi, sifre, rol, durum, pozisyon_seviye)
                    VALUES ('SİSTEM ADMİN', 'Admin', '12345', 'ADMIN', 'AKTİF', 0)
                """))
                conn.commit()
                return True
    except Exception:
        pass
    return False

def auto_fix_data():
    """Bozuk veri kayıtlarını (Örn: Unicode sorunu olan kullanıcı adları) onarır"""
    try:
        with engine.connect() as conn:
            conn.execute(text("""
                UPDATE personel
                SET kullanici_adi = 'mihrimah.ali',
                    rol = 'Personel',
                    vardiya = 'GÜNDÜZ VARDİYASI'
                WHERE id = 182 AND (rol IS NULL OR rol = '')
            """))

            # 1.5 AUTO-BOOTSTRAP EKS_MODÜLLER (Sıfır Hardcode)
            try:
                from logic.auth_logic import MODUL_ESLEME
                
                # Check exist
                mevcut_res = conn.execute(text("SELECT modul_anahtari FROM ayarlar_moduller")).fetchall()
                mevcut_anahtarlar = [r[0] for r in mevcut_res]
                
                sira = 10
                for etiket, anahtar in MODUL_ESLEME.items():
                    if anahtar not in mevcut_anahtarlar:
                        conn.execute(text("INSERT INTO ayarlar_moduller (modul_anahtari, modul_etiketi, sira_no, aktif) VALUES (:k, :e, :s, 1)"), 
                            {"k": anahtar, "e": etiket, "s": sira})
                    sira += 10
            except Exception:
                pass

            # 2. GENEL VERİ TEMİZLİĞİ
            clean_sqls = [
                "UPDATE personel SET vardiya = TRIM(vardiya) WHERE vardiya IS NOT NULL;",
                "UPDATE personel SET ad_soyad = TRIM(ad_soyad) WHERE ad_soyad IS NOT NULL;",
                "UPDATE personel SET kullanici_adi = TRIM(kullanici_adi) WHERE kullanici_adi IS NOT NULL;",
                "UPDATE ayarlar_bolumler SET bolum_adi = TRIM(bolum_adi) WHERE bolum_adi IS NOT NULL;"
            ]

            for sql in clean_sqls:
                try:
                    conn.execute(text(sql))
                except Exception:
                    pass

            conn.commit()
    except Exception:
        pass
