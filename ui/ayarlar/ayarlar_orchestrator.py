import streamlit as st
from .personel_ui import render_personel_tab, render_kullanici_tab
from .urun_ui import render_urun_tab
from .organizasyon_ui import render_rol_tab, render_yetki_tab, render_bolum_tab
from .fabrika_ui import render_lokasyon_tab, render_proses_tab
from .temizlik_gmp_ui import render_temizlik_tab, render_gmp_soru_tab
from .soguk_oda_ayarlari_ui import render_soguk_oda_ayarlari

def render_ayarlar_orchestrator(engine):
    """Ayarlar modülünün ana tab yapısını ve alt modüllerini yönetir."""
    
    st.title("⚙️ Sistem Ayarları ve Yönetim")
    st.info("Sistem genelindeki tanımlamaları, kullanıcı yetkilerini ve fabrika hiyerarşisini buradan yönetebilirsiniz.")

    # 10 Sekmeli Ana Yapı
    tabs = st.tabs([
        "👥 Personel", 
        "🔐 Kullanıcılar", 
        "📦 Ürünler", 
        "🎭 Roller", 
        "🔑 Yetkiler", 
        "🏭 Bölümler", 
        "📍 Lokasyonlar", 
        "🔧 Prosesler", 
        "🧹 Temizlik & Tanımlar", 
        "🛡️ GMP Sorular",
        "❄️ Soğuk Oda"
    ])

    with tabs[0]: render_personel_tab(engine)
    with tabs[1]: render_kullanici_tab(engine)
    with tabs[2]: render_urun_tab(engine)
    with tabs[3]: render_rol_tab(engine)
    with tabs[4]: render_yetki_tab(engine)
    with tabs[5]: render_bolum_tab(engine)
    with tabs[6]: render_lokasyon_tab(engine)
    with tabs[7]: render_proses_tab(engine)
    with tabs[8]: render_temizlik_tab(engine)
    with tabs[9]: render_gmp_soru_tab(engine)
    with tabs[10]: render_soguk_oda_ayarlari()
