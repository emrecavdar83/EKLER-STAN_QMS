
import streamlit as st

def set_branding():
    # Anayasa v3.3: Kurumsal Kimlik & PWA Scaffold
    # Kare logolar (Mobil kısayollar için zorunludur)
    SQUARE_LOGO_HD = "https://www.ekleristan.com/wp-content/uploads/2024/02/EKLERISTAN-02.png"
    FAVICON_MEDIUM = "https://www.ekleristan.com/wp-content/uploads/2024/02/EKLERISTAN-02-300x300.png"
    FAVICON_SMALL = "https://www.ekleristan.com/wp-content/uploads/2024/02/EKLERISTAN-02-150x150.png"
    
    st.set_page_config(
        page_title="Ekleristan QMS",
        page_icon=FAVICON_SMALL,
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 1. HIZLI ERİŞİM VE PWA AYARLARI (HTML Injection)
    # Bu blok tarayıcıya uygulamanın bir "Web App" gibi davranmasını söyler.
    st.markdown(f"""
        <style>
            /* Streamlit markalamasını gizle */
            #MainMenu {{visibility: hidden;}}
            footer {{visibility: hidden;}}
            header {{visibility: hidden;}}
            .stDeployButton {{display:none;}}
            
            /* Mobil scroll bar gizleme (Opsiyonel, temiz görünüm için) */
            ::-webkit-scrollbar {{ display: none; }}
        </style>
        
        <!-- Apple & Android Ana Ekran İkonları -->
        <link rel="apple-touch-icon" sizes="180x180" href="{FAVICON_MEDIUM}">
        <link rel="icon" type="image/png" sizes="32x32" href="{FAVICON_SMALL}">
        <link rel="icon" type="image/png" sizes="192x192" href="{FAVICON_MEDIUM}">
        
        <!-- Tam Ekran (Native App) Deneyimi Ayarları -->
        <meta name="apple-mobile-web-app-title" content="Ekleristan QMS">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="theme-color" content="#b40b0b"> <!-- Ekleristan Kırmızısı -->
    """, unsafe_allow_html=True)

    # 2. LOGO BAR (OPSİYONEL: Üstte her zaman görünen ince logo barı istiyorsanız buraya eklenebilir)
