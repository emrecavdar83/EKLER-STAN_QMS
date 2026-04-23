import streamlit as st
import traceback
import json
import random
import string
from datetime import datetime
from sqlalchemy import text
# from database.connection import get_engine # v6.8.9: Lazy Load and circular fix

def generate_error_id():
    """Benzersiz bir hata referans kodu üretir: #E-YYYYMMDD-XXXX"""
    date_str = datetime.now().strftime("%Y%m%d")
    rand_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"#E-{date_str}-{rand_str}"

def _yaz_blackbox_log(hata_kodu, hata_mesaji, stack_trace, modul, fonksiyon):
    """Hatayı dosya sistemine (diagnostic blackbox) yazar, max 1000 satır rotasyonu."""
    try:
        import os
        log_path = "logs/error_blackbox.log"
        os.makedirs("logs", exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\nREFERANS : {hata_kodu}\nZAMAN    : {datetime.now().isoformat()}\n"
                    f"MESAJ    : {hata_mesaji}\nMODUL    : {modul} / {fonksiyon}\nSTACK    :\n{stack_trace}\n")
        with open(log_path, "r", encoding="utf-8") as f:
            satirlar = f.readlines()
        if len(satirlar) > 1000:
            with open(log_path, "w", encoding="utf-8") as f:
                f.writelines(satirlar[-500:])
    except Exception:
        pass


def _ai_teshis_uret(stack_trace, hata_mesaji):
    """Stack trace'e bakarak insan okunabilir AI teşhisi üretir."""
    t = stack_trace
    if "NotNullViolation" in t or "NOT NULL constraint" in t:
        return "💡 Zorunlu (NOT NULL) alan boş bırakılmış. Form girişlerini kontrol edin."
    if "ForeignKeyViolation" in t or "FOREIGN KEY constraint" in t:
        return "💡 Bağlı kayıt (Foreign Key) bulunamadı. Referans verisi silinmiş olabilir."
    if "UndefinedTable" in t or "no such table" in t:
        return "💡 Veritabanında beklenen tablo yok. Migration eksik olabilir — Bakım sekmesini kontrol edin."
    if "UndefinedColumn" in t or "no such column" in t:
        return "💡 Sorgulanan kolon veritabanında yok. Yeni bir ALTER TABLE migration gerekebilir."
    if "UniqueViolation" in t or "UNIQUE constraint" in t:
        return "💡 Tekrarlı kayıt denemesi. Bu kombinasyon zaten mevcut (UNIQUE ihlali)."
    if "OperationalError" in t and "locked" in t:
        return "💡 SQLite veritabanı kilitli. Eş zamanlı yazma çakışması — birkaç saniye bekleyip tekrar deneyin."
    if "timeout" in t.lower() or "connection" in t.lower():
        return "💡 Veritabanı bağlantı zaman aşımı. Supabase/ağ bağlantısını kontrol edin."
    if "StaleDataError" in t or "could not serialize" in t:
        return "💡 Eş zamanlı güncelleme çakışması (Race Condition). Sayfayı yenileyip tekrar deneyin."
    if "KeyError" in t:
        return f"💡 Sözlük/DataFrame'de beklenen anahtar yok: {hata_mesaji[:100]}"
    if "IndexError" in t:
        return "💡 Liste veya DataFrame boş olmasına rağmen eleman erişimi yapıldı."
    if "AttributeError" in t and "NoneType" in t:
        return "💡 None değeri döndü; üzerine işlem yapılmaya çalışıldı. Boşluk kontrolü eksik."
    if "bcrypt" in t.lower() or "passlib" in t.lower():
        return "💡 Şifre doğrulama/hashleme hatası. Kullanıcının şifresini Admin üzerinden sıfırlayın."
    return f"Otomatik Analiz: {hata_mesaji[:200]}"


def _kaydet_db(engine, hata_kodu, level, modul, fonksiyon, hata_mesaji, stack_trace, context_str, ai_diagnosis, kullanici_id):
    """Hatayı hata_loglari tablosuna kaydeder. DB erişilmezse fallback log dosyasına yazar."""
    try:
        with engine.connect().execution_options(timeout=5) as conn:
            with conn.begin():
                try:
                    conn.execute(text(
                        "INSERT INTO hata_loglari (hata_kodu, seviye, modul, fonksiyon, hata_mesaji, stack_trace, context_data, ai_diagnosis, kullanici_id) "
                        "VALUES (:k, :s, :m, :f, :msg, :st, :ctx, :ai, :u)"
                    ), {"k": hata_kodu, "s": level, "m": modul, "f": fonksiyon,
                        "msg": hata_mesaji, "st": stack_trace, "ctx": context_str,
                        "ai": ai_diagnosis, "u": kullanici_id})
                except Exception:
                    conn.execute(text(
                        "INSERT INTO hata_loglari (hata_kodu, seviye, modul, fonksiyon, hata_mesaji, stack_trace, context_data) "
                        "VALUES (:k, :s, :m, :f, :msg, :st, :ctx)"
                    ), {"k": hata_kodu, "s": level, "m": modul, "f": fonksiyon,
                        "msg": hata_mesaji, "st": stack_trace, "ctx": context_str})
        return hata_kodu
    except Exception as db_err:
        import os
        with open("error_fallback.log", "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {hata_kodu} | {hata_mesaji} | {db_err}\n")
        return f"{hata_kodu}-DBLOK"


def log_error(e, level="ERROR", modul="GENEL", fonksiyon=None, context=None):
    """Hatayı blackbox + DB'ye kaydeder. Returns: hata_kodu"""
    from database.connection import get_engine
    hata_kodu    = generate_error_id()
    hata_mesaji  = str(e)
    stack_trace  = traceback.format_exc()
    kullanici_id = st.session_state.get('user_id', 0)
    context_str  = None
    if context:
        try:    context_str = json.dumps(context, default=str, ensure_ascii=False)
        except: context_str = str(context)

    _yaz_blackbox_log(hata_kodu, hata_mesaji, stack_trace, modul, fonksiyon)
    ai_diagnosis = _ai_teshis_uret(stack_trace, hata_mesaji)
    return _kaydet_db(get_engine(), hata_kodu, level, modul, fonksiyon,
                      hata_mesaji, stack_trace, context_str, ai_diagnosis, kullanici_id)

def show_ui_error(hata_kodu, user_msg="Teknik bir aksaklık oluştu."):
    """Kullanıcıya şık bir hata kutusu gösterir."""
    with st.container(border=True):
        st.error(f"### ⚠️ {user_msg}")
        st.markdown(f"""
        Sistem bu durumu otomatik olarak kayıt altına aldı. 
        Destek talebi oluştururken lütfen aşağıdaki referans kodunu bildirin:
        
        **Referans No:** `{hata_kodu}`
        """)
        if st.button("🔄 Sayfayı Yenile"):
            st.rerun()

def handle_exception(e, modul="GENEL", tip="UI"):
    """
    v4.3.5: TRANSPARENT DEBUG - Hata mesajını doğrudan UI'da göster.
    """
    if type(e).__name__ in ["StopException", "RerunException", "SwitchPageException", "TriggerRerun"]:
        raise e
        
    hata_kodu = log_error(e, modul=modul)
    if tip == "UI":
        # Hatanın ASIL sebebini de geçici olarak buraya ekliyoruz
        debug_msg = f"HATA: {str(e)}"
        show_ui_error(hata_kodu, user_msg=debug_msg)
    return hata_kodu
