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
        return create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True, 
            pool_recycle=300
        )
    else:
        # Lokal Fallback
        db_url = 'sqlite:///ekleristan_local.db'
        return create_engine(db_url, connect_args={'check_same_thread': False})

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
                id """ + ("INTEGER PRIMARY KEY AUTOINCREMENT" if not is_sqlite else "INTEGER PRIMARY KEY AUTOINCREMENT") + """,
                flow_name VARCHAR(100) UNIQUE NOT NULL,
                urun_grubu VARCHAR(100), -- Ekler, Bomba vb.
                aktif INTEGER DEFAULT 1,
                olusturulma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            # 2. Akış Düğümleri (Nodes)
            """CREATE TABLE IF NOT EXISTS flow_nodes (
                id """ + ("INTEGER PRIMARY KEY AUTOINCREMENT" if not is_sqlite else "INTEGER PRIMARY KEY AUTOINCREMENT") + """,
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
                id """ + ("INTEGER PRIMARY KEY AUTOINCREMENT" if not is_sqlite else "INTEGER PRIMARY KEY AUTOINCREMENT") + """,
                flow_id INTEGER NOT NULL,
                source_node_id INTEGER NOT NULL,
                target_node_id INTEGER NOT NULL,
                condition_rule TEXT -- Dallanma (Ekler sağa, Bomba sola)
            )""",
            # 4. Görev Atama Motoru (Task Management)
            """CREATE TABLE IF NOT EXISTS personnel_tasks (
                id """ + ("INTEGER PRIMARY KEY AUTOINCREMENT" if not is_sqlite else "INTEGER PRIMARY KEY AUTOINCREMENT") + """,
                node_id INTEGER NOT NULL,
                personel_id INTEGER NOT NULL,
                batch_id VARCHAR(100), -- Hangi parti için?
                durum VARCHAR(50) DEFAULT 'BEKLIYOR', -- BEKLIYOR, AKTIF, TAMAMLANDI, BYPASS
                atanma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tamamlanma_zamani TIMESTAMP
            )""",
            # 5. 13. Adam / Eğitim Modu Bypass Logları
            """CREATE TABLE IF NOT EXISTS flow_bypass_logs (
                id """ + ("INTEGER PRIMARY KEY AUTOINCREMENT" if not is_sqlite else "INTEGER PRIMARY KEY AUTOINCREMENT") + """,
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
                final_sql = table_sql.replace('""" + ("INTEGER PRIMARY KEY AUTOINCREMENT" if not is_sqlite else "INTEGER PRIMARY KEY AUTOINCREMENT") + """', 
                                          ("SERIAL PRIMARY KEY" if not is_sqlite else "INTEGER PRIMARY KEY AUTOINCREMENT"))
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
                    VALUES ('SİSTEM ADMİN', 'Admin', '12345', 'Admin', 'AKTİF', 0)
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
