import streamlit as st
from sqlalchemy import create_engine, text

# Yeni Modül Delegasyonu (Anayasa v6.0 Refactor)
from database.schema_master import init_all_tables, init_performans_tables
from database.migrations_master import run_migrations
from database.seed_master import bootstrap_all

def _create_engine_internal():
    """Bağlantı motorunu fiziksel olarak oluşturur."""
    db_url = st.secrets.get("DB_URL") or st.secrets.get("streamlit", {}).get("DB_URL")
    
    if db_url:
        engine = create_engine(
            db_url,
            pool_size=10, # v6.4.0: Increased for cloud stability
            max_overflow=20,
            pool_pre_ping=True, 
            pool_recycle=1800,
            connect_args={"connect_timeout": 15}
        )
        from sqlalchemy import event
        @event.listens_for(engine, "connect")
        def set_postgresql_tz(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("SET TIMEZONE='Europe/Istanbul'")
            cursor.close()
        return engine
    else:
        raise RuntimeError("CRITICAL ERROR: DB_URL not found in secrets. Live setup required.")

@st.cache_resource
def get_engine():
    """Anayasa v6.0: Merkezi giriş noktası, Delegasyon Modeli."""
    eng = _create_engine_internal()
    is_pg = eng.dialect.name == 'postgresql'
    maint_eng = eng.execution_options(isolation_level="AUTOCOMMIT") if is_pg else eng
    
    try:
        with maint_eng.connect() as conn:
            # 1. Şema Yapılandırması (Yeni Master Yapı)
            init_all_tables(conn)
            init_performans_tables(conn)
            
            # 2. Dinamik Migrasyonlar
            run_migrations(conn)
            
            # 3. Başlangıç Verileri ve Temizlik
            bootstrap_all(conn)
            
            # 4. Modül Spesifik Init'ler
            conn.commit()
        
    except Exception as e:
        print(f"[!] DATABASE_MAINTENANCE_FAILURE: {e}")
    return eng
