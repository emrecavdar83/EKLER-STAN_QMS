import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import time, pytz

from database.connection import get_engine
from logic.data_fetcher import veri_getir, run_query
from logic.auth_logic import kullanici_yetkisi_var_mi

engine = get_engine()

def get_istanbul_time():
    return datetime.now(pytz.timezone('Europe/Istanbul')) \
        if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()

def _gmp_frekans_hesapla():
    """Bugünün aktif frekanslarını döndürür (GÜNLÜK/HAFTALIK/AYLIK)."""
    simdi = get_istanbul_time()
    gun_index = simdi.weekday() # 0=Pazartesi
    ay_gunu = simdi.day

    aktif_frekanslar = ["GÜNLÜK"]
    if gun_index == 0: aktif_frekanslar.append("HAFTALIK")
    if ay_gunu == 1: aktif_frekanslar.append("AYLIK")
    
    return aktif_frekanslar, simdi

def _gmp_soru_getir(selected_lok_id, aktif_frekanslar):
    """Lokasyon ve frekansa göre soruları DB'den çeker."""
    frekans_filtre = "','".join(aktif_frekanslar)
    soru_sql = f"""
        SELECT * FROM gmp_soru_havuzu
        WHERE frekans IN ('{frekans_filtre}')
        AND aktif=TRUE
        AND (
            lokasyon_ids IS NULL
            OR ',' || lokasyon_ids || ',' LIKE '%,{selected_lok_id},%'
        )
    """
    return run_query(soru_sql)

def _gmp_denetim_formu(soru_df, selected_lok_id, lok_df):
    """Denetim formunu çizer, denetim_verileri listesi döndürür."""
    lok_adi = lok_df[lok_df['id']==selected_lok_id]['lokasyon_adi'].values[0]
    st.subheader(f"📍 {lok_adi} Denetim Soruları")
    
    denetim_verileri = []
    for idx, soru in soru_df.iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            c1.markdown(f"**{soru['soru_metni']}**")
            c1.caption(f"🏷️ Kategori: {soru['kategori']} | 📑 BRC Ref: {soru['brc_ref']} | ⚡ Risk: {soru['risk_puani']}")

            q_key_id = soru['id'] if pd.notna(soru['id']) else f"idx_{idx}"
            durum = c2.radio("Durum", ["UYGUN", "UYGUN DEĞİL"], key=f"gmp_q_{selected_lok_id}_{q_key_id}", horizontal=True)

            foto = None
            notlar = ""
            if durum == "UYGUN DEĞİL":
                if soru['risk_puani'] == 3:
                    st.warning("🚨 KRİTİK BULGU! Fotoğraf ve açıklama zorunludur.")
                    foto = st.file_uploader("⚠️ Fotoğraf Çek/Yükle", type=['jpg','png','jpeg'], key=f"foto_{selected_lok_id}_{soru['id']}")
                notlar = st.text_area("Hata Açıklaması / Düzeltici Faaliyet", key=f"not_{selected_lok_id}_{soru['id']}")

            denetim_verileri.append({
                "soru_id": soru['id'],
                "durum": durum,
                "foto": foto,
                "notlar": notlar,
                "risk": soru['risk_puani'],
                "brc": soru['brc_ref']
            })
    return denetim_verileri

def _gmp_kaydet(denetim_verileri, selected_lok_id, simdi):
    """Denetim sonuçlarını DB'ye kaydeder."""
    hata_var = False
    for d in denetim_verileri:
        if d['durum'] == "UYGUN DEĞİL" and d['risk'] == 3 and not d['foto']:
            st.error(f"Kritik sorularda fotoğraf zorunludur! (BRC: {d['brc']})")
            hata_var = True
            break

    if not hata_var:
        try:
            with engine.connect() as conn:
                for d in denetim_verileri:
                    foto_adi = f"gmp_{simdi.strftime('%Y%m%d_%H%M%S')}_{d['soru_id']}.jpg" if d['foto'] else None
                    sql = """INSERT INTO gmp_denetim_kayitlari
                             (tarih, saat, kullanici, lokasyon_id, soru_id, durum, fotograf_yolu, notlar, brc_ref, risk_puani)
                             VALUES (:t, :s, :k, :l, :q, :d, :f, :n, :b, :r)"""
                    params = {
                        "t": str(simdi.date()), "s": simdi.strftime("%H:%M"), "k": st.session_state.user,
                        "l": selected_lok_id, "q": d['soru_id'], "d": d['durum'], "f": foto_adi,
                        "n": d['notlar'], "b": d['brc'], "r": d['risk']
                    }
                    conn.execute(text(sql), params)
                conn.commit()
            st.success("✅ Denetim başarıyla kaydedildi!"); time.sleep(1.5); st.rerun()
        except Exception as e:
            st.error(f"Kaydetme hatası: {e}")

def render_gmp_module(engine):
    """Ana orkestratör."""
    if not kullanici_yetkisi_var_mi("🛡️ GMP Denetimi", "Görüntüle"):
        st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır."); st.stop()

    st.title("🛡️ GMP DENETİMİ")
    aktif_frekanslar, simdi = _gmp_frekans_hesapla()
    st.caption(f"📅 Bugünün Frekansı: {', '.join(aktif_frekanslar)}")

    try:
        lok_df = veri_getir("Tanim_Bolumler")
        if lok_df.empty:
            st.warning("⚠️ Henüz Bölüm veya Soru tanımlanmamış."); return

        lok_df = lok_df.rename(columns={'bolum_adi': 'lokasyon_adi'})
        selected_lok_id = st.selectbox("Denetim Yapılan Bölüm",
                                     options=lok_df['id'].tolist(),
                                     format_func=lambda x: lok_df[lok_df['id']==x]['lokasyon_adi'].values[0],
                                     key="gmp_lok_main")

        soru_df = _gmp_soru_getir(selected_lok_id, aktif_frekanslar)
        if soru_df.empty:
            st.warning("⚠️ Seçilen lokasyon için bugün sorulacak soru bulunmuyor."); return

        with st.form("gmp_denetim_formu"):
            denetim_verileri = _gmp_denetim_formu(soru_df, selected_lok_id, lok_df)
            if st.form_submit_button("✅ Denetimi Tamamla ve Gönder"):
                _gmp_kaydet(denetim_verileri, selected_lok_id, simdi)
    except Exception as e:
        st.error(f"Sistem Hatası: {e}")
