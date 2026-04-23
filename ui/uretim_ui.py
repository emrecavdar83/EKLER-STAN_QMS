import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import time
import pytz

from database.connection import get_engine
from logic.data_fetcher import veri_getir, run_query
from logic.auth_logic import kullanici_yetkisi_var_mi, bolum_bazli_urun_filtrele
from logic.cache_manager import clear_personnel_cache

engine = get_engine()

def get_istanbul_time():
    now = datetime.now(pytz.timezone('Europe/Istanbul')) \
        if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()
    return now.replace(microsecond=0)

_RENAME_MAP = {'saat':'Saat','vardiya':'Vardiya','urun':'Ürün Adı','lot_no':'Lot No',
               'miktar':'Miktar','fire':'Fire','kullanici':'Kaydeden','notlar':'Notlar'}


def _render_uretim_giris_formu(u_df, guvenli_kayit_ekle):
    _v = st.session_state.get('_fv_uretim_giris_form', 0)
    with st.form(f"uretim_giris_form_v{_v}"):
        col1, col2 = st.columns(2)
        f_tarih   = col1.date_input("Üretim Tarihi", get_istanbul_time())
        f_saat    = col1.text_input("Giriş Saati", get_istanbul_time().strftime("%H:%M"))
        f_vardiya = col1.selectbox("Vardiya", ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"])
        f_urun    = col1.selectbox("Üretilen Ürün", u_df['urun_adi'].unique())
        f_lot     = col2.text_input("Lot No / Parti No")
        f_miktar  = col2.number_input("Üretim Miktarı (Adet/Kg)", min_value=0.0, format="%.2f")
        f_fire    = col2.number_input("Fire Miktarı", min_value=0.0, format="%.2f")
        f_not     = col2.text_area("Üretim / Fire Detay Notu", height=150)
        if st.form_submit_button("💾 Üretimi Kaydet", width="stretch"):
            if f_lot and f_miktar > 0:
                kayit = [str(f_tarih), f_saat, f_vardiya, st.session_state.user,
                         "URETIM", f_urun, f_lot, f_miktar, f_fire, f_not, str(get_istanbul_time())]
                if guvenli_kayit_ekle("Depo_Giris_Kayitlari", kayit):
                    st.session_state['_fv_uretim_giris_form'] = _v + 1
                    st.toast(f"✅ {f_urun} üretimi başarıyla kaydedildi!"); st.rerun()
            else:
                st.warning("⚠️ Lütfen Lot No ve Miktar alanlarını doldurun.")


def _render_gunluk_uretim_izleme():
    st.subheader("📊 Günlük Üretim İzleme")
    izleme_tarih = st.columns([2, 2])[0].date_input("İzleme Tarihi", value=get_istanbul_time().date(), key="prod_view_date")
    records = veri_getir("Depo_Giris_Kayitlari")
    if records.empty:
        st.info("ℹ️ Seçilen tarihte henüz üretim kaydı bulunmuyor."); return
    records['tarih'] = pd.to_datetime(records['tarih']).dt.date
    filtered = records[records['tarih'] == izleme_tarih]
    if filtered.empty:
        st.info("ℹ️ Seçilen tarihte henüz üretim kaydı bulunmuyor."); return
    cols_to_show = [c for c in ['saat','vardiya','urun','lot_no','miktar','fire','kullanici','notlar'] if c in filtered.columns]
    ui_df = filtered[cols_to_show].copy()
    ui_df.columns = [_RENAME_MAP.get(c, c) for c in ui_df.columns]
    if st.session_state.get('screen_width', 1000) < 768:
        for _, row in ui_df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.markdown(f"**{row['Ürün Adı']}**"); c2.markdown(f"`{row['Miktar']} adet`")
                st.caption(f"🕒 {row['Saat']} | 👤 {row['Kaydeden']}")
    else:
        st.dataframe(ui_df, width="stretch", hide_index=True)
    st.info(f"📈 Toplam Üretim: {filtered['miktar'].sum():,.2f} | 📉 Toplam Fire: {filtered['fire'].sum():,.2f}")


def render_uretim_module(engine, guvenli_kayit_ekle):
    try:
        if not kullanici_yetkisi_var_mi("🏭 Üretim Girişi", "Düzenle"):
            st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır."); st.stop()
        st.title("🏭 Üretim Kayıt Girişi")
        st.caption("Günlük üretim miktarlarını ve fire detaylarını buradan işleyebilirsiniz.")
        u_df = veri_getir("Ayarlar_Urunler")
        if not u_df.empty:
            u_df.columns = [c.lower() for c in u_df.columns]
            u_df = bolum_bazli_urun_filtrele(u_df)
            _render_uretim_giris_formu(u_df, guvenli_kayit_ekle)
        else:
            st.warning("⚠️ Ürün tanımı bulunamadı. Lütfen Ayarlar > Ürün Yönetimi sayfasından ürün ekleyin.")
        st.divider()
        _render_gunluk_uretim_izleme()
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="URETIM_GIRIS", tip="UI")
