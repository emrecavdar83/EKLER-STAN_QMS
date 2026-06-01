import streamlit as st
from sqlalchemy import create_engine, text

# Yeni Modül Delegasyonu (Anayasa v6.0 Refactor)
# v6.8.9: Lazy Loading applied to prevent circular imports on Streamlit Cloud

def _create_engine_internal():
    """Bağlantı motorunu fiziksel olarak oluşturur."""
    db_url = st.secrets.get("DB_URL") or st.secrets.get("streamlit", {}).get("DB_URL")
    
    if db_url:
        # Fix deprecated postgres:// prefix (SQLAlchemy 1.4+ compatibility)
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        # Cloud stability: enforce SSL for remote databases
        connect_args = {"connect_timeout": 15}
        if "localhost" not in db_url and "127.0.0.1" not in db_url:
            connect_args["sslmode"] = "require"

        engine = create_engine(
            db_url,
            pool_size=10, # v6.4.0: Increased for cloud stability
            max_overflow=20,
            pool_pre_ping=True, 
            pool_recycle=1800,
            connect_args=connect_args
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
    """Anayasa v6.0 | v9.0 FAST BOOT: Merkezi giriş noktası.
    v9.0: 'system_v9_ready' flag ile cold start 180 round trip → 1 round trip'e düşürüldü.
    """
    eng = _create_engine_internal()
    is_pg = eng.dialect.name == 'postgresql'
    maint_eng = eng.execution_options(isolation_level="AUTOCOMMIT") if is_pg else eng

    try:
        with maint_eng.connect() as conn:
            # v9.0: FAST BOOT GATE — Sistem zaten kuruluysa 1 sorgu ile atla
            # İlk kurulumda 180 round trip çalışır ve flag set edilir.
            # Sonraki her cold start'ta: 1 SELECT → direkt engine döner.
            try:
                flag = conn.execute(text(
                    "SELECT deger FROM sistem_parametreleri "
                    "WHERE anahtar = 'system_v9_ready'"
                )).fetchone()
                if flag and flag[0] == '1':
                    print("[FAST BOOT] system_v9_ready flag detected — skipping 180 DB trips.")
                    return eng
            except Exception:
                pass  # sistem_parametreleri henüz yoksa devam et

            # --- İlk kurulum: tam init akışı ---
            from database.schema_master import init_all_tables, init_performans_tables
            from database.migrations_master import run_migrations
            from database.seed_master import bootstrap_all

            init_all_tables(conn)
            init_performans_tables(conn)
            run_migrations(conn)
            bootstrap_all(conn)

            # Başarılı kurulumu işaretle (bir sonraki boot'ta atlanacak)
            try:
                conn.execute(text(
                    "INSERT INTO sistem_parametreleri (anahtar, deger, aciklama) "
                    "VALUES ('system_v9_ready', '1', 'Fast Boot Flag — v9.0') "
                    "ON CONFLICT (anahtar) DO UPDATE SET deger = '1'"
                ))
                print("[FAST BOOT] system_v9_ready flag set. Next cold start will be instant.")
            except Exception as fe:
                print(f"[FAST BOOT] Flag set failed (non-critical): {fe}")

            conn.commit()

    except Exception as e:
        print(f"[!] DATABASE_MAINTENANCE_FAILURE: {e}")
        st.error(f"🔴 Veritabanı bağlantı hatası oluştu. Streamlit Cloud kullanıyorsanız lütfen şunları kontrol edin:\n\n"
                 f"1. **Advanced Settings > Secrets** bölümünde `DB_URL` değişkeninin doğru ayarlandığından emin olun.\n"
                 f"2. Parolanızda özel karakterler (örn. `@`, `?`, `#`) varsa URL encode (`%40` vb.) edilmiş olmalıdır.\n"
                 f"3. Veritabanı sağlayıcınızda (Neon, Supabase, vb.) IP Allowlist ayarının tüm IP'lere açık (`0.0.0.0/0`) olduğundan emin olun.\n\n"
                 f"**Hata Özeti:** `{str(e).splitlines()[0] if str(e) else 'Bilinmeyen Hata'}`")
        st.stop()
    return eng
