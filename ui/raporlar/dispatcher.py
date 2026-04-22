import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

from logic.data_fetcher import get_department_options_hierarchical, run_query
from logic.auth_logic import kullanici_yetkisi_var_mi
from logic.sync_handler import render_sync_button

def get_istanbul_time():
    return datetime.now(pytz.timezone('Europe/Istanbul')) if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()

def render_raporlama_module(engine):
    """
    EKLERİSTAN QMS - MERKEZİ RAPORLAMA DISPATCHER (v2.1)
    v2.1: Sidebar bağımlılığı kaldırıldı — matris filtreleri expander'a taşındı.
    Anayasa v5.0: Modüler yapı, Cloud-Safe SQL ve Performans Odaklı Yönlendirme.
    """
    try:
        if not kullanici_yetkisi_var_mi("📊 Kurumsal Raporlama", "Görüntüle"):
            st.error("🚫 Bu modülü görüntülemek için yetkiniz bulunmamaktadır."); st.stop()

        st.title("📊 Kurumsal Raporlama Merkezi")
        st.info("💡 Verimlilik için raporlar kategorize edilmiştir. Lütfen tarih aralığı ve kategori seçiniz.")

        def _reset_repo():
            st.session_state['goster_rapor'] = False

        c1, c2, c3 = st.columns(3)
        bas_tarih = c1.date_input("Başlangıç", get_istanbul_time().date(), on_change=_reset_repo)
        bit_tarih = c2.date_input("Bitiş", get_istanbul_time().date(), on_change=_reset_repo)
        rapor_kategorisi = c3.selectbox("Kategori", [
            "🏭 Üretim & Verimlilik",
            "🛡️ Kalite & Gıda Güvenliği",
            "❄️ Soğuk Zincir Takip",
            "🧹 Temizlik & Sanitasyon",
            "👥 İnsan Kaynakları & Org.",
            "📍 Fabrika Lokasyon & Ekipman"
        ], on_change=_reset_repo)

        # v2.1: Matris Filtreleri — sidebar yerine inline expander
        df_sahalar = run_query("SELECT id, ad as bolum_adi FROM qms_departmanlar WHERE aktif = 1 ORDER BY sira_no")
        saha_options = {0: "(Tümü)"}
        if not df_sahalar.empty:
            saha_options.update(dict(zip(df_sahalar['id'], df_sahalar['bolum_adi'])))
        dept_options = get_department_options_hierarchical()

        with st.expander("🎯 Matris Filtreleri", expanded=False):
            cf1, cf2 = st.columns(2)
            sel_saha = cf1.selectbox(
                "Operasyonel Saha",
                options=list(saha_options.keys()),
                format_func=lambda x: saha_options[x],
                on_change=_reset_repo,
                key="rapor_saha_filtre"
            )
            sel_dept = cf2.selectbox(
                "Fonksiyonel Departman",
                options=list(dept_options.keys()),
                format_func=lambda x: dept_options[x],
                on_change=_reset_repo,
                key="rapor_dept_filtre"
            )

        if st.button("Raporu Oluştur", width="stretch", type="primary"):
            st.session_state['goster_rapor'] = True

        if st.session_state.get('goster_rapor', False):
            matrix_filters = {"saha": sel_saha, "dept": sel_dept}

            # Dinamik Import ve Yönlendirme (Lazy Loading)
            if "Üretim" in rapor_kategorisi:
                from ui.raporlar.uretim_raporlari import render_uretim_sub_module
                render_uretim_sub_module(engine, bas_tarih, bit_tarih, matrix_filters)
            elif "Kalite" in rapor_kategorisi:
                from ui.raporlar.kalite_raporlari import render_kalite_sub_module
                render_kalite_sub_module(engine, bas_tarih, bit_tarih, matrix_filters)
            elif "Soğuk" in rapor_kategorisi:
                from ui.raporlar.soguk_oda_raporlari import render_soguk_oda_sub_module
                render_soguk_oda_sub_module(engine, bas_tarih, bit_tarih)
            elif "Temizlik" in rapor_kategorisi:
                from ui.raporlar.kalite_raporlari import render_kalite_sub_module
                render_kalite_sub_module(engine, bas_tarih, bit_tarih, matrix_filters, specific="temizlik")
            elif "İnsan" in rapor_kategorisi:
                from ui.raporlar.personel_raporlari import render_personel_sub_module
                render_personel_sub_module(engine, bas_tarih, bit_tarih, matrix_filters)
            elif "Lokasyon" in rapor_kategorisi:
                from ui.raporlar.lokasyon_raporlari import render_lokasyon_sub_module
                render_lokasyon_sub_module(engine)

        render_sync_button(key_prefix="raporlama_dispatch")

    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="RAPOR_DISPATCHER", tip="UI")
