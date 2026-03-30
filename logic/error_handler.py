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
    
    # Context verisini JSON'a çevir (Safety first)
    context_str = None
    if context:
        try:
            context_str = json.dumps(context, default=str, ensure_ascii=False)
        except:
            context_str = str(context)

    # AI Diagnostik (Basit başlangıç)
    ai_diagnosis = f"Otomatik Analiz: {hata_mesaji[:200]}"
    if "NotNullViolation" in stack_trace:
        ai_diagnosis = "💡 AI Teşhisi: Zorunlu (NOT NULL) bir alan boş bırakılmış. Lütfen form girişlerini kontrol edin."
    elif "ForeignKeyViolation" in stack_trace:
        ai_diagnosis = "💡 AI Teşhisi: Bağlı bir kayıt (Foreign Key) bulunamadı. Referans verisi silinmiş olabilir."
    elif "UndefinedTable" in stack_trace:
        ai_diagnosis = "💡 AI Teşhisi: Veritabanında beklenen bir tablo bulunamadı. Migration eksik olabilir."

    try:
        with engine.begin() as conn:
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
        return hata_kodu
    except Exception as db_err:
        # DB'ye yazılamazsa terminale bas ve geçici kod dön
        print(f"❌ LOG_ERROR_DB_FAILED: {db_err}")
        return f"{hata_kodu}-DBFAIL"

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
    Tek satırlık Exception handle: Logla ve UI göster.
    Kullanım: except Exception as e: handle_exception(e, 'TEMIZLIK')
    """
    hata_kodu = log_error(e, modul=modul)
    if tip == "UI":
        show_ui_error(hata_kodu)
    return hata_kodu
