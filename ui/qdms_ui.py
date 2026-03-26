# ui/qdms_ui.py
import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import json
import sys
import os

# --- S6-PROTECTOR: PTH-001 (Path Resolution) ---
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- S6-PROTECTOR: Diagnostic Import Wrapper (Unredacted Errors) ---
try:
    from database.connection import get_engine
    from modules.qdms.belge_kayit import (
        belge_olustur, 
        belge_listele, 
        belge_durum_guncelle, 
        belge_getir, 
        belge_guncelle, 
        belge_kodu_oner
    )
    from modules.qdms.revizyon import (
        revizyon_gecmisi_getir, 
        revizyon_baslat
    )
    from modules.qdms.pdf_uretici import pdf_uret
    from modules.qdms.sablon_motor import (
        sablon_getir, 
        sablon_kaydet, 
        sablon_guncelle, 
        VARSAYILAN_HEADER_CONFIG, 
        VARSAYILAN_KOLON_CONFIG_SOGUK_ODA
    )
    from modules.qdms.talimat_yonetici import (
        talimat_olustur, 
        talimat_guncelle, 
        talimat_getir_by_kod, 
        okunmayan_talimatlar, 
        okuma_onay_kaydet
    )
    from modules.qdms.uyumluluk_rapor import uyumluluk_ozeti_getir
    from logic.zone_yetki import eylem_yapabilir_mi
except Exception as e:
    st.error(f"❌ QDMS KRİTİK BAĞIMLILIK HATASI (v4.1.0): {str(e)}")
    import traceback
    st.code(traceback.format_exc())
    st.stop()

# --- YARDIMCI: Logo header ---
def _render_logo_header():
    try:
        from static.logo_b64 import LOGO_B64
        import base64
        logo_data = LOGO_B64.split(",")[1] if "," in LOGO_B64 else LOGO_B64
        img_bytes = base64.b64decode(logo_data)
        col_logo, col_title = st.columns([1, 5])
        col_logo.image(img_bytes, width=90)
        col_title.markdown("## EKLERİSTAN A.Ş.\n##### Kalite Doküman Yönetim Sistemi")
    except Exception:
        st.markdown("## EKLERİSTAN A.Ş. — QDMS")
    st.divider()

# --- CONTENT MODULES ---
def qdms_dokuman_merkezi_content(engine=None):
    if not engine: engine = get_engine()
    col1, col2, col3 = st.columns(3)
    search = col1.text_input("🔍 Belge Ara", "", key="dm_search")
    tip_list = ["Tümü", "GK", "SO", "TL", "PR", "KYS", "FR", "PL", "GT", "LS", "KL", "YD", "SOP"]
    tip_filter = col2.selectbox("Belge Tipi", tip_list, key="dm_tip")
    durum_filter = col3.selectbox("Durum", ["Tümü", "aktif", "taslak", "incelemede", "arsiv"], key="dm_durum")
    
    filtre = {}
    if durum_filter != "Tümü": filtre['durum'] = durum_filter
    belgeler = belge_listele(engine, filtre)
    df = pd.DataFrame(belgeler)
    if df.empty:
        st.info("Kriterlere uygun belge bulunamadı.")
        return
    if search:
        df = df[df['belge_adi'].str.contains(search, case=False) | df['belge_kodu'].str.contains(search, case=False)]
    
    for _, row in df.iterrows():
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 5, 2, 2])
            c1.markdown(f"**{row['belge_kodu']}**\nRev: {row['aktif_rev']}")
            c2.markdown(f"### {row['belge_adi']}\n{row['belge_tipi']} | {row['alt_kategori']}")
            color_map = {"aktif": "green", "taslak": "gray", "incelemede": "orange", "arsiv": "red"}
            color = color_map.get(row['durum'], "gray")
            c3.markdown(f":{color}[{row['durum'].upper()}]")
            if c4.button("👁️ ÖNİZLE", key=f"pre_{row['belge_kodu']}"):
                _render_belge_preview(engine, row)

def qdms_belge_yonetimi_content(engine=None):
    if not engine: engine = get_engine()
    with st.expander("➕ YENİ BELGE OLUŞTUR", expanded=False):
        with st.form("yeni_belge_form"):
            c1, c2 = st.columns(2)
            bt_list = ["GK", "SO", "TL", "PR", "KYS", "FR", "PL", "LS", "KL", "SOP"]
            b_tip = c1.selectbox("Belge Tipi", bt_list)
            b_kod = c2.text_input("Belge Kodu (Eklenecek)", value=belge_kodu_oner(engine, b_tip))
            b_ad  = st.text_input("Belge Adı")
            b_kat = st.text_input("Alt Kategori / Bölüm")
            if st.form_submit_button("Oluştur"):
                res = belge_olustur(engine, b_kod, b_ad, b_tip, b_kat, "", 1)
                if res['basarili']: 
                    st.success(f"Belge {b_kod} oluşturuldu.")
                    st.rerun()
                else: 
                    st.error(res['hata'])

    belgeler = belge_listele(engine)
    df = pd.DataFrame(belgeler)
    if not df.empty:
        st.dataframe(df[['belge_kodu', 'belge_adi', 'belge_tipi', 'durum', 'aktif_rev']], use_container_width=True)
        sel_row = st.selectbox("Düzenlenecek Belgeyi Seçin", df['belge_kodu'].tolist())
        if st.button("📝 DÜZENLEYİCİYİ AÇ"):
            _render_belge_editor(engine, df[df['belge_kodu'] == sel_row].iloc[0])

def qdms_talimat_content(engine=None):
    if not engine: engine = get_engine()
    st.subheader("📖 Talimat & SOP Yönetimi")
    t_tabs = ["Talimat Oluştur", "Onay Bekleyenler"]
    tab1, tab2 = st.tabs(t_tabs)
    with tab1:
        with st.form("talimat_form"):
            tk = st.text_input("Kod (EKL-TL-001)")
            ta = st.text_input("Adı")
            adm = st.text_area("Adımlar (JSON)", value="[]")
            if st.form_submit_button("Kaydet"):
                try:
                    res = talimat_olustur(engine, tk, ta, "Genel", json.loads(adm))
                    if res['basarili']: 
                        st.success("Talimat kaydedildi.")
                        st.rerun()
                except: 
                    st.error("JSON Hatası")

def qdms_uyumluluk_content(engine=None):
    if not engine: engine = get_engine()
    ozet = uyumluluk_ozeti_getir(engine)
    st.metric("BRC Uyum Skoru", f"%{ozet.get('brc_uyum_skoru', 0)}")
    st.progress(ozet.get('brc_uyum_skoru', 0) / 100)

def qdms_main_page(engine=None):
    st.title("📁 QDMS - Kalite Doküman Yönetim Sistemi")
    t_labels = ["📋 Doküman Merkezi", "⚙️ Yönetim", "📖 Talimatlar", "📊 Uyumluluk"]
    t1, t2, t3, t4 = st.tabs(t_labels)
    with t1: qdms_dokuman_merkezi_content(engine)
    with t2: qdms_belge_yonetimi_content(engine)
    with t3: qdms_talimat_content(engine)
    with t4: qdms_uyumluluk_content(engine)

# --- DIALOGS ---
@st.dialog("👁️ Belge Önizleme", width="large")
def _render_belge_preview(engine, row):
    st.markdown(f"### {row['belge_adi']}")
    st.divider()
    st.write(f"Kod: {row['belge_kodu']} | Rev: {row['aktif_rev']}")
    st.info(row.get('amac', 'İçerik henüz girilmemiş.'))
    if st.button("📄 PDF ÜRET & İNDİR"):
        path = pdf_uret(engine, row['belge_kodu'], row)
        with open(path, "rb") as f:
            st.download_button("İndir", f, file_name=f"{row['belge_kodu']}.pdf")

@st.dialog("📝 BRC/IFS Görev Kartı & Doküman Editörü", width="large")
def _render_belge_editor(engine, row):
    _render_logo_header()
    is_gk = str(row.get('belge_tipi','')).upper() == 'GK'
    
    if is_gk:
        from modules.qdms.gk_logic import gk_getir
        gk = gk_getir(engine, row['belge_kodu']) or {}
        with st.form(f"gk_edit_{row['belge_kodu']}"):
            sec_tabs = ["1. Profil", "2. Sorumluluklar", "3. Yetki/KPI"]
            tabs = st.tabs(sec_tabs)
            with tabs[0]:
                p1, p2 = st.columns(2)
                pa = p1.text_input("Pozisyon Adı", value=gk.get('pozisyon_adi', row['belge_adi']))
                dp = p2.text_input("Departman", value=gk.get('departman', ''))
                go = st.text_area("Görev Özeti", value=gk.get('gorev_ozeti',''))
            with tabs[1]:
                sor_txt = "\n".join([s['sorumluluk'] for s in gk.get('sorumluluklar', [])])
                sor = st.text_area("Sorumluluklar (Satır satır)", value=sor_txt)
            with tabs[2]:
                fy = st.text_input("Finansal Yetki", value=gk.get('finansal_yetki_tl', '0'))
                kpi = st.text_area("KPI'lar", value=str(gk.get('kpi_listesi', '')))
            
            if st.form_submit_button("💾 KAYDET"):
                st.success("Kaydedildi (Simülasyon)")
    else:
        current = belge_getir(engine, row['belge_kodu'])
        with st.form(f"doc_edit_{row['belge_kodu']}"):
            new_ad = st.text_input("Belge Adı", value=current['belge_adi'])
            e_ama = st.text_area("Amaç", value=current.get('amac', ''))
            e_ice = st.text_area("İçerik", value=current.get('icerik', ''))
            if st.form_submit_button("💾 GÜNCELLE"):
                res = belge_guncelle(engine, row['belge_kodu'], new_ad, current['alt_kategori'], "", amac=e_ama, icerik=e_ice)
                if res['basarili']: 
                    st.success("Güncellendi.")
                    st.rerun()

if __name__ == "__main__":
    qdms_main_page()
