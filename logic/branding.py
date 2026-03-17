
import streamlit as st

def set_branding():
    LOGO_URL = "https://www.ekleristan.com/wp-content/uploads/2024/02/logo-new.png"
    
    st.set_page_config(
        page_title="Ekleristan QMS",
        page_icon=LOGO_URL,
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Mobil cihazlar için Apple Touch Icon ve Shortcut Icon zorlaması
    # Bu HTML bloğu tarayıcıya "Ekleristan logosunu kısayol ikonu yap" talimatı gönderir.
    st.markdown(f"""
        <link rel="apple-touch-icon" href="{LOGO_URL}">
        <link rel="icon" type="image/png" href="{LOGO_URL}">
        <meta name="apple-mobile-web-app-title" content="Ekleristan QMS">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    """, unsafe_allow_html=True)
