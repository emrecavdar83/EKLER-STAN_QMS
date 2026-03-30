import streamlit as st
from ui.ayarlar.personel_ui import render_personel_tab, render_kullanici_tab
from ui.ayarlar.urun_ui import render_urun_tab
from ui.ayarlar.organizasyon_ui import render_rol_tab, render_yetki_tab, render_bolum_tab
from ui.ayarlar.fabrika_ui import render_lokasyon_tab, render_proses_tab
from ui.ayarlar.temizlik_gmp_ui import render_temizlik_tab, render_gmp_soru_tab
from ui.ayarlar.soguk_oda_ayarlari_ui import render_soguk_oda_ayarlari
from ui.ayarlar.flow_designer_ui import render_flow_designer
from ui.ayarlar.audit_log_ui import render_audit_log_module
from ui.ayarlar.bakim_ui import render_bakim_tab
from ui.ayarlar.context_ui import render_context_tab

def render_ayarlar_orchestrator(engine):
    """Ayarlar modülünün ana tab yapısını ve alt modüllerini yönetir."""
    try:
        st.title("⚙️ Sistem Ayarları ve Yönetim")
        st.info("Sistem genelindeki tanımlamaları, kullanıcı yetkilerini ve fabrika hiyerarşisini buradan yönetebilirsiniz.")

        # 13 Sekmeli Ana Yapı
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
            "❄️ Soğuk Oda",
            "🕸️ Akıllı Akış",
            "🛡️ Audit Log",
            "🔧 Sistem Bakımı",
            "📚 Bağlam (Context)"
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
        with tabs[11]: render_flow_designer(engine)
        with tabs[12]: render_audit_log_module(engine)
        with tabs[13]: render_bakim_tab(engine)
        with tabs[14]: render_context_tab(engine)
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="AYARLAR_ORCHESTRATOR", tip="UI")
