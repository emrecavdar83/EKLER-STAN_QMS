import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import text
# from logic.auth_logic import ... # v6.8.9: Lazy Load and circular fix
# from logic.zone_yetki import ... # v6.8.9: Lazy Load and circular fix
from logic.app_bootstrap import get_cookie_manager
# from static.logo_b64 import LOGO_B64 # v6.8.9: Lazy Load and circular fix

def bootstrap_session(engine):
    """v6.1.9: Handles QR, Logout signals, and Cookie-based persistence"""
    from logic.auth_logic import kalici_oturum_sil, kalici_oturum_dogrula
    from logic.zone_yetki import yetki_haritasi_yukle
    
    # 1. Logout Signal (query_params)
    if st.query_params.get("logout") == "1":
        try:
            cm = get_cookie_manager()
            token = cm.get("qms_remember_me")
            if token:
                kalici_oturum_sil(engine, token)
            cm.delete("qms_remember_me")
        except Exception:
            pass
        st.session_state.clear()
        st.query_params.clear()
        st.rerun()

    # 2. QR Deep-Linking
    if "scanned_qr" in st.query_params:
        _qr_val = st.query_params.get('scanned_qr', '').strip()
        if _qr_val:
            st.session_state.active_module_name = "❄️ Soğuk Oda Sıcaklıkları"
            st.session_state.scanned_qr_code = _qr_val
            if not st.session_state.get('logged_in'):
                st.session_state.logged_in = True
                st.session_state.user = "Saha_Mobil"
                st.session_state.user_rol = "Personel"

    # 3. Remember Me Persistence
    if not st.session_state.get('logged_in') and st.query_params.get("logout") != "1":
        try:
            remember_token = get_cookie_manager().get("qms_remember_me")
            if remember_token:
                u_data = kalici_oturum_dogrula(engine, remember_token, cihaz_bilgisi=st.context.headers.get("User-Agent", "Bilinmiyor"))
                if u_data:
                    st.session_state.logged_in = True
                    st.session_state.user = u_data.get('kullanici_adi')
                    st.session_state.user_rol = u_data.get('rol', 'Personel')
                    st.session_state.user_fullname = str(u_data.get('ad_soyad', st.session_state.user)).strip().upper()
                    st.session_state.user_id = int(u_data.get('id', 0))
                    
                    saved_module = u_data.get('son_modul', 'portal')
                    st.session_state.active_module_key = saved_module
                    
                    yetki_haritasi_yukle(engine, st.session_state.user_rol)
                    st.rerun()
        except: pass

def login_screen(engine):
    """v6.6.1: Corporate login interface with session persistence"""
    from logic.auth_logic import sifre_dogrula, audit_log_kaydet, kalici_oturum_olustur
    from logic.zone_yetki import yetki_haritasi_yukle
    from static.logo_b64 import LOGO_B64
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.image(LOGO_B64, width=200)
        st.title("🔐 EKLERİSTAN QMS")
        
        with engine.connect() as conn:
            res = conn.execute(text("SELECT id, ad_soyad, kullanici_adi, sifre, rol, durum, departman_id FROM ayarlar_kullanicilar WHERE durum='AKTİF' OR kullanici_adi='Admin'"))
            p_df = pd.DataFrame(res.fetchall(), columns=res.keys())
        p_df.columns = [c.lower().strip() for c in p_df.columns]
        users = p_df['kullanici_adi'].dropna().unique().tolist() if not p_df.empty else ["Admin"]
        user = st.selectbox("Kullanıcı Seçiniz", users)
        pwd = st.text_input("Şifre", type="password")
        remember_me = st.checkbox("Beni Hatırla (7 Gün)", value=True)
        
        if st.button("Giriş Yap", width="stretch"):
            if not p_df.empty:
                u_data = p_df[p_df['kullanici_adi'].astype(str) == str(user)]
                if not u_data.empty:
                    db_pass = str(u_data.iloc[0]['sifre']).strip().removesuffix(".0")
                    if sifre_dogrula(str(pwd).strip(), db_pass, user, engine=engine):
                        if str(u_data.iloc[0].get('durum')).upper() not in ['AKTİF', 'TRUE']:
                            st.error("⛔ Hesabınız PASİF durumdadır.")
                        else:
                            st.session_state.logged_in = True
                            st.session_state.user = user
                            st.session_state.user_rol = u_data.iloc[0].get('rol', 'Personel')
                            st.session_state.user_fullname = str(u_data.iloc[0].get('ad_soyad', user)).strip().upper()
                            st.session_state.user_id = int(u_data.iloc[0]['id'])
                            st.session_state.user_dept_id = int(u_data.iloc[0]['departman_id']) if not pd.isna(u_data.iloc[0]['departman_id']) else None
                            st.session_state.active_module_key = "portal"
                            yetki_haritasi_yukle(engine, st.session_state.user_rol)
                            audit_log_kaydet("OTURUM_ACILDI", f"{user} giriş yaptı.")
                            
                            if remember_me:
                                token = kalici_oturum_olustur(engine, int(u_data.iloc[0]['id']), 
                                                               st.context.headers.get("User-Agent", "Bilinmiyor"),
                                                               son_modul=st.session_state.get('active_module_key', 'portal'))
                                get_cookie_manager().set("qms_remember_me", token, expires_at=datetime.now() + timedelta(days=7))
                            st.rerun()
                    else: st.error("❌ Hatalı Şifre!")
                else: st.error("❓ Kullanıcı bulunamadı.")

def guvenli_cikis_yap(engine):
    """Beni Hatırla döngüsünü kıran ve tüm oturum izlerini silen tahliye fonksiyonu."""
    try:
        from logic.auth_logic import kalici_oturum_sil
        cm = get_cookie_manager()
        token = cm.get("qms_remember_me")
        if token:
            kalici_oturum_sil(engine, token)
        cm.delete("qms_remember_me")
    except: pass
    
    st.query_params["logout"] = "1"
    st.session_state.logged_in = False
    st.rerun()
