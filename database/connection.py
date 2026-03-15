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
    is_pg = eng.dialect.name == 'postgresql'
    
    # 🧪 QUANTUM SPEED: Tek bir metadata sorgusu ile tüm eksikleri bul (Orta Çağ'dan çıkış)
    with eng.connect() as conn:
        try:
            # 1. Mevcut Tabloları Çek
            if is_pg:
                res_tabs = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
            else:
                res_tabs = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
            existing_tables = {r[0].lower() for r in res_tabs}

            # 2. Kritik Kolonları Çek
            if is_pg:
                res_cols = conn.execute(text("SELECT table_name, column_name FROM information_schema.columns WHERE table_schema = 'public'")).fetchall()
            else:
                # SQLite için her ana tabloyu tek tek sormak yerine sadece gerekli olanlara bakacağız (Daha hızlı)
                res_cols = []
                for t in ['urun_kpi_kontrol', 'sicaklik_olcumleri', 'ayarlar_roller', 'personel', 'ayarlar_bolumler', 'map_vardiya']:
                    if t in existing_tables:
                        c_res = conn.execute(text(f"PRAGMA table_info({t})")).fetchall()
                        for c in c_res: res_cols.append((t, c[1]))
            
            existing_cols = {(r[0].lower(), r[1].lower()) for r in res_cols}

            # 3. SADECE EKSİK OLANLARI ÇALIŞTIR
            with conn.execution_options(isolation_level="AUTOCOMMIT") if is_pg else conn:
                # Kolon Migrasyonları
                mig_list = [
                    ("urun_kpi_kontrol", "fotograf_b64", "ALTER TABLE urun_kpi_kontrol ADD COLUMN fotograf_b64 TEXT"),
                    ("sicaklik_olcumleri", "planlanan_zaman", "ALTER TABLE sicaklik_olcumleri ADD COLUMN planlanan_zaman TIMESTAMP"),
                    ("sicaklik_olcumleri", "qr_ile_girildi", "ALTER TABLE sicaklik_olcumleri ADD COLUMN qr_ile_girildi INTEGER DEFAULT 1"),
                    ("ayarlar_roller", "aktif", "ALTER TABLE ayarlar_roller ADD COLUMN aktif INTEGER DEFAULT 1"),
                    ("personel", "guncelleme_tarihi", "ALTER TABLE personel ADD COLUMN guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                    ("ayarlar_bolumler", "guncelleme_tarihi", "ALTER TABLE ayarlar_bolumler ADD COLUMN guncelleme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
                    ("map_vardiya", "acan_kullanici_id", "ALTER TABLE map_vardiya ADD COLUMN acan_kullanici_id INTEGER"),
                    ("map_vardiya", "kapatan_kullanici_id", "ALTER TABLE map_vardiya ADD COLUMN kapatan_kullanici_id INTEGER")
                ]
                for tbl, col, sql in mig_list:
                    if (tbl, col) not in existing_cols:
                        try: conn.execute(text(sql))
                        except Exception: pass

                # Hayalet Tablolar (Shadow Tables)
                shadow_tabs = [
                    ('sistem_loglari', """CREATE TABLE sistem_loglari (id SERIAL_PK_PLACEHOLDER, islem_tipi VARCHAR(50), detay TEXT, zaman TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"""),
                    ('lokasyon_tipleri', """CREATE TABLE lokasyon_tipleri (id SERIAL_PK_PLACEHOLDER, tip_adi VARCHAR(50) UNIQUE NOT NULL, sira_no INTEGER DEFAULT 10, aktif INTEGER DEFAULT 1)"""),
                    ('vardiya_tipleri', """CREATE TABLE vardiya_tipleri (id SERIAL_PK_PLACEHOLDER, tip_adi VARCHAR(50) UNIQUE NOT NULL, sira_no INTEGER DEFAULT 10, aktif INTEGER DEFAULT 1)"""),
                    ('izin_gunleri_tipleri', """CREATE TABLE izin_gunleri_tipleri (id SERIAL_PK_PLACEHOLDER, tip_adi VARCHAR(50) UNIQUE NOT NULL, sira_no INTEGER DEFAULT 10, aktif INTEGER DEFAULT 1)""")
                ]
                _pk_sub = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
                for t_name, t_sql in shadow_tabs:
                    if t_name not in existing_tables:
                        try: conn.execute(text(t_sql.replace("SERIAL_PK_PLACEHOLDER", _pk_sub)))
                        except Exception: pass
        except Exception as e:
            print(f"Quantum Migration Error: {e}")
            # Fallback kalsın (Garantici yaklaşım)
                
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
        
        # 4. MAP & PERFORMANS TABLOLARI
        _pk = "SERIAL PRIMARY KEY" if is_pg else "INTEGER PRIMARY KEY AUTOINCREMENT"
        _ts = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP" if is_pg else "TEXT DEFAULT (datetime('now','localtime'))"
        
        # Sadece eksikse tablo oluştur
        if 'map_vardiya' not in existing_tables:
            conn.execute(text(f"""CREATE TABLE map_vardiya (
                id {_pk}, tarih TEXT NOT NULL, makina_no TEXT NOT NULL DEFAULT 'MAP-01',
                vardiya_no INTEGER NOT NULL, baslangic_saati TEXT NOT NULL, bitis_saati TEXT,
                operator_adi TEXT NOT NULL, acan_kullanici_id INTEGER, kapatan_kullanici_id INTEGER,
                vardiya_sefi TEXT, besleme_kisi INTEGER DEFAULT 0,
                kasalama_kisi INTEGER DEFAULT 0, hedef_hiz_paket_dk REAL DEFAULT 4.2,
                gerceklesen_uretim INTEGER DEFAULT 0, durum TEXT DEFAULT 'ACIK', notlar TEXT,
                olusturma_ts {_ts}, guncelleme_ts {_ts}
            )"""))

        if 'map_zaman_cizelgesi' not in existing_tables:
            conn.execute(text(f"""CREATE TABLE map_zaman_cizelgesi (
                id {_pk}, vardiya_id INTEGER NOT NULL REFERENCES map_vardiya(id),
                sira_no INTEGER NOT NULL, baslangic_ts TEXT NOT NULL, bitis_ts TEXT,
                sure_dk REAL, durum TEXT NOT NULL, neden TEXT, aciklama TEXT, olusturma_ts {_ts}
            )"""))

        if 'map_bobin_kaydi' not in existing_tables:
            conn.execute(text(f"""CREATE TABLE map_bobin_kaydi (
                id {_pk}, vardiya_id INTEGER NOT NULL REFERENCES map_vardiya(id),
                sira_no INTEGER NOT NULL, degisim_ts TEXT NOT NULL, bobin_lot TEXT,
                baslangic_m REAL DEFAULT 300, bitis_m REAL, kullanilan_m REAL, aciklama TEXT, olusturma_ts {_ts}
            )"""))

        if 'map_fire_kaydi' not in existing_tables:
            conn.execute(text(f"""CREATE TABLE map_fire_kaydi (
                id {_pk}, vardiya_id INTEGER NOT NULL REFERENCES map_vardiya(id),
                fire_tipi TEXT NOT NULL, miktar_adet INTEGER NOT NULL DEFAULT 0,
                bobin_ref TEXT, aciklama TEXT, olusturma_ts {_ts}
            )"""))

        if 'performans_degerledirme' not in existing_tables:
            conn.execute(text(f"""CREATE TABLE performans_degerledirme (
                id {_pk}, uuid TEXT UNIQUE NOT NULL, personel_id INTEGER, calisan_adi_soyadi TEXT NOT NULL, bolum TEXT NOT NULL,
                gorevi TEXT NOT NULL, ise_giris_tarihi DATE, donem TEXT NOT NULL, degerlendirme_tarihi DATE NOT NULL, degerlendirme_yili INTEGER NOT NULL,
                kkd_kullanimi INTEGER, mesleki_kriter_2 INTEGER, mesleki_kriter_3 INTEGER, mesleki_kriter_4 INTEGER, mesleki_kriter_5 INTEGER,
                mesleki_kriter_6 INTEGER, mesleki_kriter_7 INTEGER, mesleki_kriter_8 INTEGER, mesleki_ortalama_puan REAL, calisma_saatleri_uyum INTEGER,
                ogrenme_kabiliyeti INTEGER, iletisim_becerisi INTEGER, problem_cozme INTEGER, kalite_bilinci INTEGER, ise_baglilik_aidiyet INTEGER,
                ekip_calismasi_uyum INTEGER, verimli_calisma INTEGER, kurumsal_ortalama_puan REAL, agirlikli_toplam_puan REAL NOT NULL,
                polivalans_duzeyi TEXT NOT NULL, polivalans_kodu INTEGER NOT NULL, yorum TEXT, degerlendiren_adi TEXT,
                olusturma_tarihi {_ts}, guncelleme_tarihi {_ts}, guncelleyen_kullanici TEXT, surum INTEGER DEFAULT 1, onceki_puan REAL,
                sync_durumu TEXT DEFAULT 'bekliyor', silinmis INTEGER DEFAULT 0
            )"""))

        if 'polivalans_matris' not in existing_tables:
            conn.execute(text(f"""CREATE TABLE polivalans_matris (
                id {_pk}, personel_id INTEGER, calisan_adi TEXT NOT NULL, bolum TEXT NOT NULL, gorevi TEXT NOT NULL, guncelleme_yili INTEGER NOT NULL,
                son_puan_d1 REAL, son_puan_d2 REAL, yil_ortalama REAL, polivalans_kodu INTEGER, polivalans_metni TEXT, puan_degisimi REAL,
                egitim_ihtiyaci INTEGER DEFAULT 0, olusturma_tarihi {_ts}, sync_durumu TEXT DEFAULT 'bekliyor'
            )"""))


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
