import streamlit as st
import pandas as pd
from datetime import datetime
from .performans_sabitleri import KRITER_ETIKETLERI, MESLEKI_KRITERLER, KURUMSAL_KRITERLER, DONEM_SECENEKLERI, POLIVALANS_RENKLERI
from . import performans_hesap as hesap

def calisan_bilgi_formu(personel_df: pd.DataFrame):
    """Personel seçim formu."""
    if personel_df.empty:
        st.error("Sistemde aktif ayarlar_kullanicilar bulunamadı.")
        return None
    
    with st.container(border=True):
        st.subheader("📋 Personel ve Dönem")
        c1, c2 = st.columns(2)
        
        pers_dict = {row['id']: f"{row['ad_soyad']} ({row['bolum']})" for _, row in personel_df.iterrows()}
        selected_id = c1.selectbox("Personel Seçin", options=list(pers_dict.keys()), format_func=lambda x: pers_dict[x])
        p_data = personel_df[personel_df['id'] == selected_id].iloc[0].to_dict()
        
        donem = c2.selectbox("Değerlendirme Dönemi", DONEM_SECENEKLERI)
        yil = c2.number_input("Yıl", 2020, 2100, datetime.now().year)
        tarih = c1.date_input("Değerlendirme Tarihi", datetime.now().date())
        
        return {
            "personel_id": selected_id,
            "calisan_adi_soyadi": p_data['ad_soyad'],
            "bolum": p_data['bolum'],
            "gorevi": p_data['gorev'],
            "ise_giris_tarihi": str(p_data['ise_giris_tarihi']),
            "donem": donem,
            "degerlendirme_yili": yil,
            "degerlendirme_tarihi": str(tarih)
        }

def puan_giris_formu():
    """Mesleki ve Kurumsal puan girişi."""
    puanlar = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🛠️ Mesleki Teknik (%70)")
        for k in MESLEKI_KRITERLER:
            label = KRITER_ETIKETLERI.get(k, k)
            puanlar[k] = st.slider(label, 0, 100, 70, key=f"sld_{k}")
            
    with col2:
        st.markdown("### 🏢 Kurumsal Nitelikler (%30)")
        for k in KURUMSAL_KRITERLER:
            label = KRITER_ETIKETLERI.get(k, k)
            puanlar[k] = st.slider(label, 0, 100, 70, key=f"sld_{k}")
            
    return puanlar

def degerlendirme_ozet_karti(puanlar: dict):
    """Anlık hesaplama ve özet kartı."""
    m_ort = hesap.mesleki_ortalama_hesapla(puanlar)
    k_ort = hesap.kurumsal_ortalama_hesapla(puanlar)
    t_puan = hesap.agirlikli_toplam_hesapla(m_ort, k_ort)
    seviye = hesap.polivalans_duzeyi_belirle(t_puan)
    
    with st.container(border=True):
        st.markdown(f"### Sonuç: **{t_puan}** Puan")
        c1, c2, c3 = st.columns(3)
        c1.metric("Mesleki (%70)", f"{m_ort / 0.7:.1f}/100")
        c2.metric("Kurumsal (%30)", f"{k_ort / 0.3:.1f}/100")
        c3.metric("Düzey", f"KOD {seviye['kod']}")
        
        st.markdown(f"""
        <div style="background:{seviye['renk']}; color:white; padding:10px; border-radius:5px; text-align:center; font-weight:bold;">
            {seviye['metin']}
        </div>
        """, unsafe_allow_html=True)
        
    return {
        "mesleki_ortalama_puan": m_ort,
        "kurumsal_ortalama_puan": k_ort,
        "agirlikli_toplam_puan": t_puan,
        "polivalans_duzeyi": seviye['metin'],
        "polivalans_kodu": seviye['kod']
    }
