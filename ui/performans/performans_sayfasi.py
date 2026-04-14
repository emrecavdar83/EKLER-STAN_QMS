# modules/performans/performans_sayfasi.py
import streamlit as st
import pandas as pd
from datetime import datetime
from . import performans_db as db
from . import performans_form as form
from . import performans_sabitleri as sabit
from database.connection import get_engine
from logic.auth_logic import kullanici_yetkisi_var_mi


def _puan_to_renk(val):
    """Polivalans kodu (1-5) → CSS renk string'i."""
    if pd.isna(val):
        return ''
    renk = sabit.POLIVALANS_RENKLERI.get(int(val), '#CCCCCC')
    return f'background-color: {renk}; color: white; font-weight: bold; text-align: center;'


def _render_polivalans_matrisi(df):
    """Kişi × Dönem pivot tablosu, renk kodlu polivalans_kodu."""
    st.subheader("🟩 Polivalans Yetkinlik Matrisi")
    if df.empty:
        st.info("Bu yıl için değerlendirme verisi bulunamadı.")
        return
    pivot = df.pivot_table(
        index='calisan_adi_soyadi', columns='donem',
        values='polivalans_kodu', aggfunc='last'
    ).reset_index()
    donem_cols = [c for c in pivot.columns if c != 'calisan_adi_soyadi']
    styled = pivot.style.applymap(_puan_to_renk, subset=donem_cols)
    st.dataframe(styled, width="stretch", hide_index=True)
    legend_cols = st.columns(5)
    for i, (sev, bilgi) in enumerate(sabit.POLIVALANS_ESLIKLERI.items()):
        legend_cols[i].markdown(
            f"<b style='background:{bilgi['renk']};padding:2px 5px;color:white;border-radius:3px'>&nbsp;{sev}&nbsp;</b>&nbsp;{bilgi['metin'][:28]}",
            unsafe_allow_html=True
        )


def _render_bolum_ozeti(df):
    """Bölüm bazlı ortalama ağırlıklı puan bar chart."""
    st.subheader("🏭 Bölüm Bazlı Ortalama")
    if df.empty:
        st.info("Veri yok.")
        return
    ozet = df.groupby('bolum')['agirlikli_toplam_puan'].mean().round(1)
    st.bar_chart(ozet)


def _render_trend_analizi(df):
    """1. Dönem vs 2. Dönem ortalama karşılaştırması."""
    st.subheader("📊 Dönem Trendi")
    if df.empty or 'donem' not in df.columns:
        st.info("Veri yok.")
        return
    if df['donem'].nunique() < 2:
        st.info("Trend için en az 2 dönem verisi gereklidir.")
        return
    trend = df.groupby('donem')['agirlikli_toplam_puan'].mean().round(1)
    st.bar_chart(trend)


def _render_analiz_matris(engine):
    """TAB 3 ana render fonksiyonu: yıl filtresi + 3 bileşen."""
    yil = st.number_input("Analiz Yılı", 2020, 2100, datetime.now().year, key="matris_yil")
    df = db.matris_verisi_getir(engine, yil)
    _render_polivalans_matrisi(df)
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        _render_bolum_ozeti(df)
    with c2:
        _render_trend_analizi(df)

def performans_sayfasi_goster():
    """📈 Yetkinlik & Performans Yönetimi Modülü"""
    try:
        st.title("📈 Yetkinlik & Performans Yönetimi")
        st.caption("Personel Yetkinlik ve Polivalans Takip Sistemi")
        
        engine = get_engine()
        
        # v5.8.16: Case-Insensitive Admin & Zone Check
        user_rol = str(st.session_state.get('user_rol', 'PERSONEL')).upper().strip()
        
        if user_rol != 'ADMIN':
            if not kullanici_yetkisi_var_mi("performans_polivalans", "Görüntüle"):
                st.error("Bu modüle erişim yetkiniz bulunmamaktadır.")
                return

        tabs = st.tabs(["➕ Yeni Değerlendirme", "📋 Geçmiş Kayıtlar", "📈 Analiz & Matris"])
        
        # --- TAB 1: YENİ DEĞERLENDİRME ---
        with tabs[0]:
            if not kullanici_yetkisi_var_mi("performans_polivalans", "Düzenle"):
                st.warning("Değerlendirme girmek için 'Düzenle' yetkisi gereklidir.")
            else:
                p_df = db.personel_listesi_getir(engine)
                bilgi = form.calisan_bilgi_formu(p_df)
                
                if bilgi:
                    puanlar = form.puan_giris_formu()
                    sonuc = form.degerlendirme_ozet_karti(puanlar)
                    
                    yorum = st.text_area("🗒️ Değerlendirme Yorumu & Notlar")
                    
                    if st.button("💾 DEĞERLENDİRMEYİ KAYDET", width="stretch", type="primary"):
                        # Veriyi birleştir
                        final_data = {**bilgi, **puanlar, **sonuc}
                        final_data['yorum'] = yorum
                        final_data['degerlendiren_adi'] = st.session_state.get('user', 'Sistem')
                        final_data['guncelleyen_kullanici'] = st.session_state.get('user', 'Sistem')
                        
                        ok, msg = db.degerlendirme_kaydet(engine, final_data)
                        if ok:
                            st.success(msg)
                            st.balloons()
                        else:
                            st.error(msg)

        # --- TAB 2: GEÇMİŞ KAYITLAR ---
        with tabs[1]:
            st.subheader("🔍 Kayıt Sorgulama")
            c1, c2 = st.columns(2)
            f_bolum = c1.selectbox("Bölüm Filtresi", ["Tümü"] + db.bolum_listesi_getir(engine))
            f_yil = c2.number_input("Yıl Filtresi", 2020, 2100, datetime.now().year, key="f_yil")
            
            filtre = {}
            if f_bolum != "Tümü": filtre['bolum'] = f_bolum
            filtre['yil'] = f_yil
            
            liste_df = db.degerlendirme_listele(engine, filtre)
            if not liste_df.empty:
                st.dataframe(liste_df[[
                    'degerlendirme_tarihi', 'calisan_adi_soyadi', 'bolum', 
                    'agirlikli_toplam_puan', 'polivalans_duzeyi', 'degerlendiren_adi'
                ]], width="stretch", hide_index=True)
            else:
                st.info("Kayıt bulunamadı.")

        # --- TAB 3: ANALİZ & MATRİS ---
        with tabs[2]:
            _render_analiz_matris(engine)
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="PERFORMANS_MAIN", tip="UI")
        st.error(f"Sistem hatası: {e}")
