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
        "ALTER TABLE sicaklik_olcumleri ADD COLUMN qr_ile_girildi INTEGER DEFAULT 1"
    ]
    with eng.begin() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
            except Exception:
                pass
                
        # PostgreSQL Sequence Senkronizasyonu (Veri aktarımı sonrası ID çakışmalarını önlemek için)
        if eng.dialect.name == 'postgresql':
            tables_to_sync = [
                'hijyen_kontrol_kayitlari', 'depo_giris_kayitlari', 'urun_kpi_kontrol', 
                'sicaklik_olcumleri', 'olcum_plani', 'temizlik_kayitlari', 'personel'
            ]
            for tbl in tables_to_sync:
                try:
                    sync_sql = f"SELECT setval(pg_get_serial_sequence('{tbl}', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM {tbl};"
                    conn.execute(text(sync_sql))
                except Exception as e:
                    pass

# Global engine nesnesi
engine = init_connection()
auto_migrate_schema(engine)

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
            # 1. Mihrimah Ali (ID 182) Fix
            conn.execute(text("""
                UPDATE personel
                SET kullanici_adi = 'mihrimah.ali',
                    rol = 'Personel',
                    vardiya = 'GÜNDÜZ VARDİYASI'
                WHERE id = 182 AND (rol IS NULL OR rol = '')
            """))

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
