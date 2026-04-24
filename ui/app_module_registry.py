import streamlit as st
from logic.zone_yetki import zone_girebilir_mi
from logic.db_writer import guvenli_kayit_ekle, guvenli_coklu_kayit_ekle


def _zone_gate(z):
    from logic.zone_yetki import _normalize_rol
    if _normalize_rol(st.session_state.get('user_rol')) == 'ADMIN':
        return
    if not zone_girebilir_mi(z):
        st.error(f"🚫 '{z.upper()}' bölgesine erişim yetkiniz bulunmamaktadır.")
        st.stop()


def _portal_dispatch(engine, m_key):
    if m_key == "portal":
        from ui.portal.portal_ui import render_portal_module; render_portal_module(engine); return True
    if m_key == "profilim":
        from ui.profil_ui import render_profil_modulu; render_profil_modulu(engine); return True
    return False


def _ops_dispatch(engine, m_key):
    if m_key == "uretim_girisi":
        _zone_gate('ops'); from ui.uretim_ui import render_uretim_module; render_uretim_module(engine, guvenli_kayit_ekle); return True
    if m_key == "personel_hijyen":
        from ui.hijyen_ui import render_hijyen_module; render_hijyen_module(engine, guvenli_coklu_kayit_ekle); return True
    if m_key == "temizlik_kontrol":
        from ui.temizlik_ui import render_temizlik_module; render_temizlik_module(engine); return True
    if m_key == "soguk_oda":
        from ui.soguk_oda_ui import render_sosts_module; render_sosts_module(engine); return True
    if m_key == "map_uretim":
        from ui.map_uretim.map_uretim import render_map_module; render_map_module(engine); return True
    if m_key == "gunluk_gorevler":
        from modules.gunluk_gorev.ui import render_gunluk_gorev_modulu; render_gunluk_gorev_modulu(engine); return True
    if m_key == "personel_vardiya_yonetimi":
        from modules.vardiya.ui import render_vardiya_module; render_vardiya_module(engine); return True
    return False


def _mgt_dispatch(engine, m_key):
    if m_key == "qdms":
        _zone_gate('mgt'); from ui.qdms_ui import qdms_main_page; qdms_main_page(engine); return True
    if m_key == "kpi_kontrol":
        _zone_gate('mgt'); from ui.kpi_ui import render_kpi_module; render_kpi_module(engine, guvenli_kayit_ekle); return True
    if m_key == "gmp_denetimi":
        _zone_gate('mgt'); from ui.gmp_ui import render_gmp_module; render_gmp_module(engine); return True
    if m_key == "kurumsal_raporlama":
        _zone_gate('mgt'); from ui.raporlar.dispatcher import render_raporlama_module; render_raporlama_module(engine); return True
    if m_key == "performans_polivalans":
        _zone_gate('mgt'); from ui.performans.performans_sayfasi import performans_sayfasi_goster; performans_sayfasi_goster(); return True
    if m_key == "denetim_izi":
        _zone_gate('mgt'); from ui.denetim_izi_ui import render_denetim_izi_module; render_denetim_izi_module(engine); return True
    return False


def _sys_dispatch(engine, m_key):
    if m_key == "ayarlar":
        _zone_gate('sys'); from ui.ayarlar.ayarlar_orchestrator import render_ayarlar_orchestrator; render_ayarlar_orchestrator(engine); return True
    if m_key == "anayasa":
        _zone_gate('sys'); from ui.anayasa_ui import render_anayasa_module; render_anayasa_module(engine); return True
    return False


def render_module_dispatcher(engine, m_key):
    try:
        with st.empty().container():
            _portal_dispatch(engine, m_key) or _ops_dispatch(engine, m_key) or \
            _mgt_dispatch(engine, m_key) or _sys_dispatch(engine, m_key)
    except Exception as e:
        if type(e).__name__ in ["StopException", "RerunException", "SwitchPageException", "TriggerRerun"]:
            raise e
        from logic.error_handler import handle_exception
        handle_exception(e, modul="MODULE_DISPATCHER", tip="UI")
