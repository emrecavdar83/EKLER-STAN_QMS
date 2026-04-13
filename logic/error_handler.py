import streamlit as st
import traceback
import json
import random
import string
from datetime import datetime
from sqlalchemy import text
from database.connection import get_engine

def generate_error_id():
    """Benzersiz bir hata referans kodu üretir: #E-YYYYMMDD-XXXX"""
    date_str = datetime.now().strftime("%Y%m%d")
    rand_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"#E-{date_str}-{rand_str}"

def log_error(e, level="ERROR", modul="GENEL", fonksiyon=None, context=None):
    """
    Hatayı veritabanına (hata_loglari) kaydeder.
    Returns: hata_kodu
    """
    engine = get_engine()
    hata_kodu = generate_error_id()
    hata_mesaji = str(e)
    stack_trace = traceback.format_exc()
    kullanici_id = st.session_state.get('user_id', 0)
    
    # v5.9.0: DIAGNOSTIC BLACK BOX — append modu, max 500 satır rotasyonu
    try:
        log_path = "logs/error_blackbox.log"
        import os; os.makedirs("logs", exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"REFERANS : {hata_kodu}\n")
            f.write(f"ZAMAN    : {datetime.now().isoformat()}\n")
            f.write(f"MESAJ    : {hata_mesaji}\n")
            f.write(f"MODUL    : {modul} / {fonksiyon}\n")
            f.write(f"STACK    :\n{stack_trace}\n")
        # Boyut koruması: 1000 satırı aşarsa son 500'ü tut
        with open(log_path, "r", encoding="utf-8") as f:
            satirlar = f.readlines()
        if len(satirlar) > 1000:
            with open(log_path, "w", encoding="utf-8") as f:
                f.writelines(satirlar[-500:])
    except Exception:
        pass

    # Context verisini JSON'a çevir (Safety first)
    context_str = None
    if context:
        try:
            context_str = json.dumps(context, default=str, ensure_ascii=False)
        except Exception:
            context_str = str(context)

    # v5.9.0: Genişletilmiş AI Teşhis Motoru
    ai_diagnosis = f"Otomatik Analiz: {hata_mesaji[:200]}"
    trace_txt = stack_trace  # kısaltma
    if "NotNullViolation" in trace_txt or "NOT NULL constraint" in trace_txt:
        ai_diagnosis = "💡 Zorunlu (NOT NULL) alan boş bırakılmış. Form girişlerini kontrol edin."
    elif "ForeignKeyViolation" in trace_txt or "FOREIGN KEY constraint" in trace_txt:
        ai_diagnosis = "💡 Bağlı kayıt (Foreign Key) bulunamadı. Referans verisi silinmiş olabilir."
    elif "UndefinedTable" in trace_txt or "no such table" in trace_txt:
        ai_diagnosis = "💡 Veritabanında beklenen tablo yok. Migration eksik olabilir — Bakım sekmesini kontrol edin."
    elif "UndefinedColumn" in trace_txt or "no such column" in trace_txt:
        ai_diagnosis = "💡 Sorgulanan kolon veritabanında yok. Yeni bir ALTER TABLE migration gerekebilir."
    elif "UniqueViolation" in trace_txt or "UNIQUE constraint" in trace_txt:
        ai_diagnosis = "💡 Tekrarlı kayıt denemesi. Bu kombinasyon zaten mevcut (UNIQUE ihlali)."
    elif "OperationalError" in trace_txt and "locked" in trace_txt:
        ai_diagnosis = "💡 SQLite veritabanı kilitli. Eş zamanlı yazma çakışması — birkaç saniye bekleyip tekrar deneyin."
    elif "timeout" in trace_txt.lower() or "connection" in trace_txt.lower():
        ai_diagnosis = "💡 Veritabanı bağlantı zaman aşımı. Supabase/ağ bağlantısını kontrol edin."
    elif "StaleDataError" in trace_txt or "could not serialize" in trace_txt:
        ai_diagnosis = "💡 Eş zamanlı güncelleme çakışması (Race Condition). Sayfayı yenileyip tekrar deneyin."
    elif "KeyError" in trace_txt:
        ai_diagnosis = f"💡 Sözlük/DataFrame'de beklenen anahtar yok: {hata_mesaji[:100]}"
    elif "IndexError" in trace_txt:
        ai_diagnosis = "💡 Liste veya DataFrame boş olmasına rağmen eleman erişimi yapıldı."
    elif "AttributeError" in trace_txt and "NoneType" in trace_txt:
        ai_diagnosis = "💡 None değeri döndü; üzerine işlem yapılmaya çalışıldı. Boşluk kontrolü eksik."
    elif "bcrypt" in trace_txt.lower() or "passlib" in trace_txt.lower():
        ai_diagnosis = "💡 Şifre doğrulama/hashleme hatası. Kullanıcının şifresini Admin üzerinden sıfırlayın."

    # v4.0.7: RESILIENT LOGGING (Non-blocking DB access)
    try:
        # SQLite için kısa timeout denemesi (SQLAlchemy 2.x üzerinden)
        with engine.connect().execution_options(timeout=5) as conn:
            with conn.begin():
                # 1. Tam Set Denemesi
                try:
                    sql = text("""
                        INSERT INTO hata_loglari 
                        (hata_kodu, seviye, modul, fonksiyon, hata_mesaji, stack_trace, context_data, ai_diagnosis, kullanici_id)
                        VALUES (:k, :s, :m, :f, :msg, :st, :ctx, :ai, :u)
                    """)
                    conn.execute(sql, {
                        "k": hata_kodu, "s": level, "m": modul, "f": fonksiyon, 
                        "msg": hata_mesaji, "st": stack_trace, "ctx": context_str, 
                        "ai": ai_diagnosis, "u": kullanici_id
                    })
                except Exception:
                    # 2. Kısıtlı Set Denemesi (Eski şema uyumu)
                    sql_min = text("""
                        INSERT INTO hata_loglari 
                        (hata_kodu, seviye, modul, fonksiyon, hata_mesaji, stack_trace, context_data)
                        VALUES (:k, :s, :m, :f, :msg, :st, :ctx)
                    """)
                    conn.execute(sql_min, {
                        "k": hata_kodu, "s": level, "m": modul, "f": fonksiyon, 
                        "msg": hata_mesaji, "st": stack_trace, "ctx": context_str
                    })
        return hata_kodu
    except Exception as db_err:
        # DB kilitliyse veya ulaşılamıyorsa sistemi tıkama (Blokaj önleyici)
        import os
        log_file = "error_fallback.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {hata_kodu} | {hata_mesaji} | {db_err}\n")
        print(f"❌ LOG_ERROR_NON_BLOCKING_FALLBACK: {db_err}")
        return f"{hata_kodu}-DBLOK"

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
