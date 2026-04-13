import streamlit as st
from datetime import datetime
from sqlalchemy import text
from logic.auth_logic import audit_log_kaydet
import soguk_oda_utils

def sosts_bakim_calistir(engine, tetikleyen_kullanici):
    """
    ANAYASA v3.5: plan_uret + kontrol_geciken_olcumler çalıştırır.
    Ağır işlemleri UI thread'inden ayırmak için manuel tetiklenir.
    """
    try:
        # Ağır işlemler
        soguk_oda_utils.plan_uret(engine)
        soguk_oda_utils.kontrol_geciken_olcumler(engine)
        
        # Log ve Durum
        audit_log_kaydet(
            "SOSTS_BAKIM",
            "Manuel SOSTS bakımı başarıyla tamamlandı.",
            tetikleyen_kullanici
        )
        _son_bakim_guncelle(engine)
        
        # Session state güncelle (Anlık UI tepkisi için)
        st.session_state['sosts_last_maintenance'] = datetime.now().timestamp()
        
        return {'basarili': True}
    except Exception as e:
        audit_log_kaydet("SOSTS_BAKIM_HATA", f"Bakım sırasında hata: {str(e)}", tetikleyen_kullanici)
        return {'basarili': False, 'hata': str(e)}

def son_bakim_zamani_getir(engine) -> datetime:
    """sistem_parametreleri'nden son bakım zamanını okur."""
    try:
        with engine.connect() as conn:
            sql = text("SELECT param_degeri FROM sistem_parametreleri WHERE param_adi = 'sosts_son_bakim_ts'")
            res = conn.execute(sql).scalar()
            if res:
                return datetime.fromisoformat(res)
    except Exception:
        pass
    return None

def _son_bakim_guncelle(engine):
    """sistem_parametreleri'ne şu anki zamanı yazar."""
    now_iso = datetime.now().isoformat()
    try:
        with engine.begin() as conn:
            # Tablo var mı kontrolü (Bootstrap güvenliği)
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS sistem_parametreleri (
                    param_adi VARCHAR(100) PRIMARY KEY,
                    param_degeri TEXT,
                    guncelleme_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Upsert (SQLite & Postgres uyumlu genel mantık)
            res = conn.execute(text("UPDATE sistem_parametreleri SET param_degeri = :val, guncelleme_ts = CURRENT_TIMESTAMP WHERE param_adi = :key"), {"val": now_iso, "key": 'sosts_son_bakim_ts'})
            if res.rowcount == 0:
                conn.execute(text("INSERT INTO sistem_parametreleri (param_adi, param_degeri) VALUES (:key, :val)"), {"key": 'sosts_son_bakim_ts', "val": now_iso})
    except Exception as e:
        print(f"Update Maintenance TS Error: {e}")
