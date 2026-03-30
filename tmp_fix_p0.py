import os

path = r"c:\Projeler\S_program\EKLERİSTAN_QMS\app.py"
if not os.path.exists(path):
    print(f"ERROR: {path} not found.")
    exit()

with open(path, "r", encoding="utf-8") as f:
    text = f.read()

# Daha güvenli bir replacer: login_screen bittikten sonra main_app'in navigasyon kısmını hedefle
old_nav_marker_start = "st.session_state.available_modules = modul_listesi"
old_nav_marker_end = "# --- MODÜL YERLEŞTİRME (DISPATCHER) ---"

start_pos = text.find(old_nav_marker_start)
end_pos = text.find(old_nav_marker_end)

if start_pos != -1 and end_pos != -1:
    # Marker'dan bir satır sonrasına geç
    start_pos += len(old_nav_marker_start)
    
    new_nav_block = """
    # --- v4.0.7.3: Streamlit Cloud P0 Navigation Fix ---
    if 'active_module_key' not in st.session_state:
        st.session_state.active_module_key = "portal"
    
    current_label = SLUG_TO_LABEL.get(st.session_state.active_module_key, modul_listesi[0])
    st.session_state.sidebar_nav = current_label
    st.session_state.quick_nav = current_label

    c1, mid, c2 = st.columns([1, 2, 1])
    with c1:
        if st.session_state.active_module_key != "portal":
            if st.button("🏠 Ana Sayfa", use_container_width=True, key="global_home_btn"):
                st.session_state.active_module_key = "portal"
                st.rerun()
    with mid:
        if st.session_state.active_module_key in SLUG_TO_LABEL:
            st.caption(f"📍 Yol: {SLUG_TO_LABEL[st.session_state.active_module_key]}")
    with c2:
        def sync_from_quick():
            label = st.session_state.quick_nav
            st.session_state.active_module_key = LABEL_TO_SLUG.get(label, "portal")
            audit_log_kaydet("NAVIGASYON", f"Hızlı Eriş: {label}")
        st.selectbox("🚀 HIZLI", modul_listesi, label_visibility="collapsed", key="quick_nav", on_change=sync_from_quick)

    st.markdown("---")

    with st.sidebar:
        st.image(LOGO_B64)
        st.write(f"👤 **{st.session_state.user}**")
        if st.button("🚪 Sistemi Kapat (Logout)", use_container_width=True, key="logout_btn"):
            from logic.auth_logic import kalici_oturum_sil
            rt = cookie_manager_obj.get("qms_remember_me")
            if rt:
                kalici_oturum_sil(engine, rt)
                cookie_manager_obj.delete("qms_remember_me")
            st.session_state.logged_in = False
            st.session_state.user = ""
            st.rerun()
        st.markdown("---")
        if st.session_state.get('user_rol') == 'ADMIN':
            st.caption(f"⚡ Yetki DB Sorgu Sayısı: {sorgu_sayisini_getir()}")
        def sync_from_sidebar():
            label = st.session_state.sidebar_nav
            st.session_state.active_module_key = LABEL_TO_SLUG.get(label, "portal")
            audit_log_kaydet("NAVIGASYON", f"Yan Menü: {label}")
        st.radio("🏠 ANA MENÜ", modul_listesi, key="sidebar_nav", on_change=sync_from_sidebar)

    st.markdown("---")
    """
    
    updated_text = text[:start_pos] + new_nav_block + text[end_pos:]
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(updated_text)
    print("SUCCESS: app.py partially rewritten with safe nav block.")
else:
    print(f"ERROR: Markers not found. start={start_pos}, end={end_pos}")
