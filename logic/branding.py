
import streamlit as st

def set_branding():
    # Anayasa v4.1: Kurumsal Kimlik & Premium UI Scaffold
    # (Config sorumluluğu app.py'ye devredilmiştir)

    # 1. PREMIUM CSS ENJEKSİYONU (Inter Font & Glassmorphism)
    st.markdown("""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=Outfit:wght@500;700&display=swap" rel="stylesheet">
        
        <style>
            /* --- GLOBAL MODERNIZATION --- */
            html, body, [class*="css"] {
                font-family: 'Inter', sans-serif !important;
                background-color: #f8f9fa;
            }
            
            h1, h2, h3, .stHeader {
                font-family: 'Outfit', sans-serif !important;
                color: #1e293b;
            }

            /* Streamlit markalamasını gizle */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            .stDeployButton {display:none;}
            
            /* --- PREMIUM HEADER (Sticky Glassmorphism) --- */
            .corporate-header {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                z-index: 999996;
                padding: 10px 30px;
                background: rgba(255, 255, 255, 0.85);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border-bottom: 1px solid rgba(180, 11, 11, 0.2);
                display: flex;
                align-items: center;
                justify-content: space-between;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
            }
            
            .header-left {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            
            .header-logo {
                height: 42px;
                width: auto;
            }
            
            .header-title {
                font-family: 'Outfit', sans-serif;
                font-weight: 700;
                font-size: 1.4rem;
                color: #b40b0b;
                letter-spacing: 1.5px;
                margin: 0;
                padding-left: 15px;
                border-left: 2px solid #b40b0b;
            }
            
            /* --- PREMIUM BUTTONS --- */
            div.stButton > button {
                border-radius: 8px !important;
                font-weight: 600 !important;
                transition: all 0.3s ease !important;
                border: none !important;
                box-shadow: 0 4px 6px rgba(180, 11, 11, 0.1) !important;
            }
            
            div.stButton > button:hover {
                transform: translateY(-2px) !important;
                box-shadow: 0 6px 12px rgba(180, 11, 11, 0.2) !important;
                background-color: #a00a0a !important;
            }

            /* Sidebar Modernization */
            [data-testid="stSidebar"] {
                background-color: #ffffff !important;
                border-right: 1px solid #e2e8f0 !important;
            }
            
            /* Add padding to top of main content to handle fixed header */
            .main .block-container {
                padding-top: 5rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

def render_corporate_header():
    """Tüm sayfalarda en üstte kurumsal marka deneyimi sunar."""
    try:
        from static.logo_b64 import LOGO_B64
        
        # v4.1.0-STABILIZE: Safe asset injection
        # Büyük base64 string'ini f-string içinde taşımak yerine parçalı yapı kullanıyoruz.
        logo_tag = f'<img src="{LOGO_B64}" class="header-logo" alt="Logo">'
        
        header_html = f"""
        <div class="corporate-header">
            <div class="header-left">
                {logo_tag}
                <div class="header-title">EKLERİSTAN QMS</div>
            </div>
            <div class="header-right">
                <span style="font-size: 0.75rem; color: #64748b; font-weight: 600; opacity: 0.8;">
                    V5.8.11 PREMIUM
                </span>
            </div>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)
    except Exception as e:
        # Fail-silent for branding (Don't crash the whole app if logo fails)
        st.write("---") # Fallback to a simple divider
