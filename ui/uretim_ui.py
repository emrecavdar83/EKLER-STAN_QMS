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

def render_uretim_module(engine, guvenli_kayit_ekle):
    """
    Üretim Kayıt Girişi modülünü render eder.
    app.py'den ui/uretim_ui.py'a taşınmıştır.
    """
    if not kullanici_yetkisi_var_mi("🏭 Üretim Girişi", "Düzenle"):
        st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır."); st.stop()

    st.title("🏭 Üretim Kayıt Girişi")
    st.caption("Günlük üretim miktarlarını ve fire detaylarını buradan işleyebilirsiniz.")

    # Ürün Listesini Çek (Teknik Doküman: Ayarlar_Urunler)
    u_df = veri_getir("Ayarlar_Urunler")

    if not u_df.empty:
        # Sütun isimlerini küçült (standardizasyon)
        u_df.columns = [c.lower() for c in u_df.columns]
        # Sorumlu departman filtresi (Teknik dökümana göre iş kuralı 6.2)
        u_df = bolum_bazli_urun_filtrele(u_df)

        with st.form("uretim_giris_form"):
            col1, col2 = st.columns(2)
            f_tarih = col1.date_input("Üretim Tarihi", get_istanbul_time())
            f_saat = col1.text_input("Giriş Saati", get_istanbul_time().strftime("%H:%M"))
            f_vardiya = col1.selectbox("Vardiya", ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"])
            f_urun = col1.selectbox("Üretilen Ürün", u_df['urun_adi'].unique())

            f_lot = col2.text_input("Lot No / Parti No")
            f_miktar = col2.number_input("Üretim Miktarı (Adet/Kg)", min_value=0.0, format="%.2f")
            f_fire = col2.number_input("Fire Miktarı", min_value=0.0, format="%.2f")
            f_not = col2.text_area("Üretim / Fire Detay Notu", help="Üretim detaylarını veya fire nedenlerini buraya detaylıca yazabilirsiniz.", height=150)

            if st.form_submit_button("💾 Üretimi Kaydet", use_container_width=True):
                if f_lot and f_miktar > 0:
                    # Teknik Doküman Tablo: Depo_Giris_Kayitlari
                    yeni_kayit = [
                        str(f_tarih),
                        f_saat,
                        f_vardiya,
                        st.session_state.user,
                        "URETIM",
                        f_urun,
                        f_lot,
                        f_miktar,
                        f_fire,
                        f_not,
                        str(get_istanbul_time())
                    ]
                    if guvenli_kayit_ekle("Depo_Giris_Kayitlari", yeni_kayit):
                        st.toast(f"✅ {f_urun} üretimi başarıyla kaydedildi!"); st.rerun()
                else:
                    st.warning("⚠️ Lütfen Lot No ve Miktar alanlarını doldurun.")

    st.divider()
    st.subheader("📊 Günlük Üretim İzleme")

    # Filtreleme Barı
    f_col1, f_col2 = st.columns([2, 2])
    izleme_tarih = f_col1.date_input("İzleme Tarihi", value=get_istanbul_time().date(), key="prod_view_date")

    # Kayıtları Getir
    records = veri_getir("Depo_Giris_Kayitlari")
    if not records.empty:
        records['tarih'] = pd.to_datetime(records['tarih']).dt.date
        filtered = records[records['tarih'] == izleme_tarih]

        if not filtered.empty:
            # UI'da Teknik Doküman Sütunlarını Sadeleştirerek Göster
            cols_to_show = ['saat', 'vardiya', 'urun', 'lot_no', 'miktar', 'fire', 'kullanici', 'notlar']
            present_cols = [c for c in cols_to_show if c in filtered.columns]
            ui_df = filtered[present_cols].copy()

            # Sütun isimlerini Türkçeleştir
            rename_map = {
                'saat': 'Saat',
                'vardiya': 'Vardiya',
                'urun': 'Ürün Adı',
                'lot_no': 'Lot No',
                'miktar': 'Miktar',
                'fire': 'Fire',
                'kullanici': 'Kaydeden',
                'notlar': 'Notlar'
            }
            ui_df.columns = [rename_map.get(c, c) for c in ui_df.columns]
            # v3.1: Mobil Duyarlı Görünüm (Responsive View)
            is_mobile = st.session_state.get('screen_width', 1000) < 768
            
            if is_mobile:
                st.write("---")
                for _, row in ui_df.iterrows():
                    with st.container(border=True):
                        c1, c2 = st.columns([3, 1])
                        c1.markdown(f"**{row['Ürün Adı']}**")
                        c2.markdown(f"`{row['Miktar']} adet`")
                        st.caption(f"🕒 {row['Saat']} | 👤 {row['Kaydeden']}")
            else:
                st.dataframe(ui_df, use_container_width=True, hide_index=True)

            # Toplamlar
            t_mikt = filtered['miktar'].sum()
            t_fire = filtered['fire'].sum()
            st.info(f"📈 Toplam Üretim: {t_mikt:,.2f} | 📉 Toplam Fire: {t_fire:,.2f}")
        else:
            st.info("ℹ️ Seçilen tarihte henüz üretim kaydı bulunmuyor.")
    else:
        st.warning("⚠️ Ürün tanımı bulunamadı. Lütfen Ayarlar > Ürün Yönetimi sayfasından ürün ekleyin.")
