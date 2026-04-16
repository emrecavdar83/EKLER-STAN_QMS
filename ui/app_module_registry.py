import streamlit as st
from logic.zone_yetki import zone_girebilir_mi
from logic.db_writer import guvenli_kayit_ekle, guvenli_coklu_kayit_ekle

def render_module_dispatcher(engine, m_key):
    """
    v6.1.9: Centralized module orchestration with zone-gating.
    Replaces the 60+ line elif block in app.py.
    """
    try:
        def zone_gate(z):
            if not zone_girebilir_mi(z):
                st.error(f"🚫 '{z.upper()}' bölgesine erişim yetkiniz bulunmamaktadır.")
                st.stop()

        _module_slot = st.empty()
        with _module_slot.container():
            if m_key == "portal":
                from ui.portal.portal_ui import render_portal_module
                render_portal_module(engine)
            elif m_key == "uretim_girisi":
                zone_gate('ops')
                from ui.uretim_ui import render_uretim_module
                render_uretim_module(engine, guvenli_kayit_ekle)
            elif m_key == "qdms":
                zone_gate('mgt')
                from ui.qdms_ui import qdms_main_page
                qdms_main_page(engine)
            elif m_key == "kpi_kontrol":
                zone_gate('mgt')
                from ui.kpi_ui import render_kpi_module
                render_kpi_module(engine, guvenli_kayit_ekle)
            elif m_key == "gmp_denetimi":
                zone_gate('mgt')
                from ui.gmp_ui import render_gmp_module
                render_gmp_module(engine)
            elif m_key == "personel_hijyen":
                from ui.hijyen_ui import render_hijyen_module
                render_hijyen_module(engine, guvenli_coklu_kayit_ekle)
            elif m_key == "temizlik_kontrol":
                from ui.temizlik_ui import render_temizlik_module
                render_temizlik_module(engine)
            elif m_key == "kurumsal_raporlama":
                zone_gate('mgt')
                from ui.raporlar.dispatcher import render_raporlama_module
                render_raporlama_module(engine)
            elif m_key == "soguk_oda":
                from ui.soguk_oda_ui import render_sosts_module
                render_sosts_module(engine)
            elif m_key == "map_uretim":
                from ui.map_uretim.map_uretim import render_map_module
                render_map_module(engine)
            elif m_key == "gunluk_gorevler":
                from modules.gunluk_gorev.ui import render_gunluk_gorev_modulu
                render_gunluk_gorev_modulu(engine)
            elif m_key == "personel_vardiya_yonetimi":
                from modules.vardiya.ui import render_vardiya_module
                render_vardiya_module(engine)
            elif m_key == "performans_polivalans":
                zone_gate('mgt')
                from ui.performans.performans_sayfasi import performans_sayfasi_goster
                performans_sayfasi_goster()
            elif m_key == "denetim_izi":
                zone_gate('mgt')
                from ui.denetim_izi_ui import render_denetim_izi_module
                render_denetim_izi_module(engine)
            elif m_key == "ayarlar":
                zone_gate('sys')
                from ui.ayarlar.ayarlar_orchestrator import render_ayarlar_orchestrator
                render_ayarlar_orchestrator(engine)
            elif m_key == "profilim":
                from ui.profil_ui import render_profil_modulu
                render_profil_modulu(engine)
    except Exception as e:
        e_type = type(e).__name__
        if e_type in ["StopException", "RerunException", "SwitchPageException", "TriggerRerun"]:
            raise e
        from logic.error_handler import handle_exception
        handle_exception(e, modul="MODULE_DISPATCHER", tip="UI")
