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

# --- S6-PROTECTOR: Diagnostic Import Wrapper ---
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
    from modules.qdms.gk_logic import gk_getir, gk_kaydet
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
    st.error(f"❌ QDMS KRİTİK BAĞIMLILIK HATASI (v4.1.1): {str(e)}")
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
            # S6-PROTECTOR: REG-001 (One-Click PDF Button Restored)
            c1, c2, c3, c4, c5 = st.columns([2, 4, 1, 1, 2])
            c1.markdown(f"**{row['belge_kodu']}**\nRev: {row['aktif_rev']}")
            c2.markdown(f"### {row['belge_adi']}\n{row['belge_tipi']} | {row['alt_kategori']}")
            color_map = {"aktif": "green", "taslak": "gray", "incelemede": "orange", "arsiv": "red"}
            color = color_map.get(row['durum'], "gray")
            c3.markdown(f":{color}[{row['durum'].upper()}]")
            
            # PDF BUTONU (Direkt)
            if c4.button("📄 PDF", key=f"pdf_{row['belge_kodu']}"):
                with st.spinner("PDF Hazırlanıyor..."):
                    # v4.1.9: Sadece liste verisi yetmez, tam metadata ve alt tablo verilerini çek (PDF-DATA-001)
                    if str(row.get('belge_tipi','')).upper() == 'GK':
                        full_veri = gk_getir(engine, row['belge_kodu'])
                    else:
                        full_veri = belge_getir(engine, row['belge_kodu'])
                    
                    if not full_veri:
                        st.error("Döküman verisi veritabanından çekilemedi.")
                    else:
                        # row'daki diğer listeleme bilgilerini de ekle (rev_no, durum vb.)
                        full_veri['rev_no'] = row.get('aktif_rev', '01')
                        full_veri['durum'] = row.get('durum', 'aktif')
                        
                        path = pdf_uret(engine, row['belge_kodu'], full_veri)
                        with open(path, "rb") as f:
                            pdf_bytes = f.read()
                        st.download_button("📥 İndir", pdf_bytes, file_name=f"{row['belge_kodu']}.pdf", key=f"dl_{row['belge_kodu']}", mime="application/pdf")
            
            if c5.button("👁️ ÖNİZLE", key=f"pre_{row['belge_kodu']}"):
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
    
    # GK Özel Önizleme
    is_gk = row['belge_tipi'] == 'GK'
    if is_gk:
        from modules.qdms.gk_logic import gk_getir
        gk = gk_getir(engine, row['belge_kodu'])
        if gk:
            tabs = st.tabs(["1-3. Profil & Özet", "4. Sorumluluklar", "5-7. Yetki & Etkileşim", "8-10. Yetkinlik & KPI"])
            
            with tabs[0]:
                st.markdown(f"**Pozisyon:** {gk.get('pozisyon_adi','-')}")
                st.markdown(f"**Departman:** {gk.get('departman','-')}")
                st.markdown(f"**Amir:** {gk.get('bagli_pozisyon','-')} | **Vekil:** {gk.get('vekalet_eden','-')}")
                st.markdown(f"**Çalışma Yeri:** {gk.get('zone','-')} | **Vardiya:** {gk.get('vardiya_turu','-')}")
                st.divider()
                st.markdown(f"**GÖREV ÖZETİ:**\n\n{gk.get('gorev_ozeti','-')}")

            with tabs[1]:
                sor_list = gk.get('sorumluluklar', [])
                disciplines = {
                    'personel': '👥 Personel', 'operasyon': '⚙️ Operasyon', 
                    'gida_guvenligi': '🛡️ Gıda Güvenliği', 'isg': '⚠️ İSG', 'cevre': '🌱 Çevre'
                }
                for d_key, d_label in disciplines.items():
                    sub = [s for s in sor_list if s.get('disiplin_tipi') == d_key]
                    if sub:
                        st.markdown(f"**{d_label}**")
                        for s in sub:
                            st.write(f"• {s['sorumluluk']}")
                            if s.get('etkilesim_birimleri'):
                                st.caption(f"Etkileşim: {s['etkilesim_birimleri']}")

            with tabs[2]:
                c1, c2 = st.columns(2)
                c1.markdown("**5. YETKİ SINIRLARI**")
                c1.write(f"• Finansal: {gk.get('finansal_yetki_tl','0')} TL")
                c1.write(f"• İmza: {gk.get('imza_yetkisi','-')}")
                c2.markdown("**6. ETKİLEŞİM (RACI)**")
                for e in gk.get('etkilesimler', []):
                    c2.write(f"• {e['taraf']}: {e['konu']} ({e['raci_rol']})")
                st.divider()
                st.markdown("**7. PERİYODİK GÖREVLER**")
                for g in gk.get('periyodik_gorevler', []):
                    st.write(f"• {g['gorev_adi']} ({g['periyot']}) - {g.get('talimat_kodu','')}")

            with tabs[3]:
                st.markdown("**8. NİTELİK VE YETKİNLİK**")
                st.write(f"• Eğitim: {gk.get('min_egitim','-')}")
                st.write(f"• Deneyim: {gk.get('min_deneyim_yil','0')} Yıl")
                st.write(f"• Sertifikalar: {gk.get('zorunlu_sertifikalar',[])}")
                st.divider()
                st.markdown("**9. PERFORMANS (KPI)**")
                for k in gk.get('kpi_listesi', []):
                    st.write(f"• {k['kpi_adi']}: {k['hedef_deger']} {k['olcum_birimi']}")
                st.divider()
                st.markdown("**10. ONAY**")
                st.caption("Onay süreçleri 'Yönetim' paneli üzerinden takip edilmektedir.")
    else:
        st.info(row.get('amac', 'İçerik henüz girilmemiş.'))

@st.dialog("📝 BRC/IFS Görev Kartı & Doküman Editörü", width="large")
def _render_belge_editor(engine, row):
    _render_logo_header()
    is_gk = str(row.get('belge_tipi','')).upper() == 'GK'
    
    if is_gk:
        # S6-PROTECTOR: DRI-001 (10-Section Architecture Full Implementation)
        from modules.qdms.gk_logic import gk_getir, gk_kaydet
        gk = gk_getir(engine, row['belge_kodu']) or {}
        
        # Sorumlulukları disiplinlere göre ayır
        sor_list = gk.get('sorumluluklar', [])
        s_pers = "\n".join([s['sorumluluk'] for s in sor_list if s.get('disiplin_tipi') == 'personel'])
        s_oper = "\n".join([s['sorumluluk'] for s in sor_list if s.get('disiplin_tipi') == 'operasyon'])
        s_gida = "\n".join([s['sorumluluk'] for s in sor_list if s.get('disiplin_tipi') == 'gida_guvenligi'])
        s_isg  = "\n".join([s['sorumluluk'] for s in sor_list if s.get('disiplin_tipi') == 'isg'])
        s_cevre = "\n".join([s['sorumluluk'] for s in sor_list if s.get('disiplin_tipi') == 'cevre'])

        with st.form(f"gk_edit_{row['belge_kodu']}"):
            st.markdown("### 📋 Görev Kartı Editörü (Madde 19)")
            sec_tabs = st.tabs([
                "1-2. Profil", "3. Özet", "4. Sorumluluklar", 
                "5. Yetkiler", "6. Etkileşim", "7. Periyodik", 
                "8. Nitelik", "9. KPI"
            ])
            
            with sec_tabs[0]:
                c1, c2 = st.columns(2)
                p_adi = c1.text_input("Pozisyon Adı", value=gk.get('pozisyon_adi', row['belge_adi']))
                dept = c2.text_input("Departman", value=gk.get('departman', ''))
                bp = c1.text_input("Bağlı Pozisyon (Amir)", value=gk.get('bagli_pozisyon', ''))
                ve = c2.text_input("Vekâlet Eden", value=gk.get('vekalet_eden', ''))
                zn = c1.text_input("Zone / Çalışma Yeri", value=gk.get('zone', ''))
                vt = c2.text_input("Vardiya Türü", value=gk.get('vardiya_turu', ''))

            with sec_tabs[1]:
                goz = st.text_area("3. GENEL GÖREV AMACI / ÖZETİ", value=gk.get('gorev_ozeti',''))

            with sec_tabs[2]:
                st.info("Her satıra bir sorumluluk gelecek şekilde giriniz.")
                t_pers = st.text_area("👥 Personel Sorumlulukları", value=s_pers)
                t_oper = st.text_area("⚙️ Operasyonel Sorumluluklar", value=s_oper)
                t_gida = st.text_area("🛡️ Gıda Güvenliği Sorumlulukları", value=s_gida)
                t_isg  = st.text_area("⚠️ İSG Sorumlulukları", value=s_isg)
                t_cevre = st.text_area("🌱 Çevre Sorumlulukları", value=s_cevre)

            with sec_tabs[3]:
                f_yet = st.text_input("Finansal Yetki (TL)", value=gk.get('finansal_yetki_tl', '0'))
                i_yet = st.text_area("İmza Yetkisi", value=gk.get('imza_yetkisi', ''))
                v_kos = st.text_area("Vekâlet Koşulları", value=gk.get('vekalet_kosullari', ''))

            with sec_tabs[4]:
                st.caption("Format: Taraf | Konu | Sıklık | RACI (Her satıra bir adet)")
                etk_raw = "\n".join([f"{e['taraf']} | {e['konu']} | {e.get('siklik','-')} | {e['raci_rol']}" for e in gk.get('etkilesimler', [])])
                retk = st.text_area("Süreçler Arası Etkileşim", value=etk_raw)

            with sec_tabs[5]:
                st.caption("Format: Görev Adı | Periyot | Talimat Kodu | Sertifikasyon (Her satıra bir adet)")
                per_raw = "\n".join([f"{g['gorev_adi']} | {g['periyot']} | {g.get('talimat_kodu','-')} | {g.get('sertifikasyon_maddesi','-')}" for g in gk.get('periyodik_gorevler', [])])
                pgor = st.text_area("7. Periyodik Görevler", value=per_raw)

            with sec_tabs[6]:
                min_e = st.text_input("Eğitim Gereksinimi", value=gk.get('min_egitim', ''))
                min_d = st.number_input("Min. Deneyim (Yıl)", value=int(gk.get('min_deneyim_yil', 0)))
                z_sert = st.text_area("Zorunlu Sertifikalar (JSON Liste)", value=json.dumps(gk.get('zorunlu_sertifikalar', [])))
                t_nit = st.text_area("Tercihli Nitelikler", value=gk.get('tercihli_nitelikler', ''))

            with sec_tabs[7]:
                st.caption("Format: KPI Adı | Birim | Hedef | Periyot | Değerlendirici (Her satıra bir adet)")
                kpi_raw = "\n".join([f"{k['kpi_adi']} | {k['olcum_birimi']} | {k['hedef_deger']} | {k['degerlendirme_periyodu']} | {k.get('degerlendirici','-')}" for k in gk.get('kpi_listesi', [])])
                kpi_t = st.text_area("9. Performans Göstergeleri (KPI)", value=kpi_raw)

            if st.form_submit_button("💾 GÖREV KARTINI KAYDET VE YAYINLA"):
                try:
                    # Yeni veri sözlüğünü oluştur
                    yeni_veri = {
                        "belge_kodu": row['belge_kodu'],
                        "pozisyon_adi": p_adi,
                        "departman": dept,
                        "bagli_pozisyon": bp,
                        "vekalet_eden": ve,
                        "zone": zn,
                        "vardiya_turu": vt,
                        "gorev_ozeti": goz,
                        "finansal_yetki_tl": f_yet,
                        "imza_yetkisi": i_yet,
                        "vekalet_kosullari": v_kos,
                        "min_egitim": min_e,
                        "min_deneyim_yil": min_d,
                        "zorunlu_sertifikalar": json.loads(z_sert),
                        "tercihli_nitelikler": t_nit,
                        "olusturan_id": st.session_state.get('user_id', 1),
                        "sorumluluklar": [],
                        "etkilesimler": [],
                        "periyodik_gorevler": [],
                        "kpi_listesi": []
                    }
                    
                    # Sorumlulukları parse et
                    mapping = [('personel', t_pers), ('operasyon', t_oper), ('gida_guvenligi', t_gida), ('isg', t_isg), ('cevre', t_cevre)]
                    idx = 1
                    for d_tip, text in mapping:
                        for line in text.strip().split('\n'):
                            if line.strip():
                                yeni_veri['sorumluluklar'].append({
                                    "disiplin_tipi": d_tip, "kategori": d_tip.upper(),
                                    "sira_no": idx, "sorumluluk": line.strip()
                                })
                                idx += 1
                                
                    # Etkileşimleri parse et
                    for line in retk.strip().split('\n'):
                        parts = line.split('|')
                        if len(parts) >= 4:
                            yeni_veri['etkilesimler'].append({"taraf": parts[0].strip(), "konu": parts[1].strip(), "siklik": parts[2].strip(), "raci_rol": parts[3].strip()})
                            
                    # Periyodik görevleri parse et
                    for line in pgor.strip().split('\n'):
                        parts = line.split('|')
                        if len(parts) >= 4:
                            yeni_veri['periyodik_gorevler'].append({"gorev_adi": parts[0].strip(), "periyot": parts[1].strip(), "talimat_kodu": parts[2].strip(), "sertifikasyon_maddesi": parts[3].strip()})
                            
                    # KPI parse et
                    for line in kpi_t.strip().split('\n'):
                        parts = line.split('|')
                        if len(parts) >= 5:
                            yeni_veri['kpi_listesi'].append({"kpi_adi": parts[0].strip(), "olcum_birimi": parts[1].strip(), "hedef_deger": parts[2].strip(), "degerlendirme_periyodu": parts[3].strip(), "degerlendirici": parts[4].strip()})

                    res = gk_kaydet(engine, yeni_veri)
                    if res['basarili']:
                        st.success("✅ Görev Kartı başarıyla güncellendi ve Supabase üzerine kaydedildi.")
                        st.rerun()
                    else:
                        st.error(f"❌ Kayıt Hatası: {res['hata']}")
                except Exception as ex:
                    st.error(f"❌ Veri İşleme Hatası: {str(ex)}")
    else:
        current = belge_getir(engine, row['belge_kodu'])
        with st.form(f"doc_edit_{row['belge_kodu']}"):
            new_ad = st.text_input("Belge Adı", value=current['belge_adi'])
            e_ama = st.text_area("1. AMAÇ", value=current.get('amac', ''))
            e_ice = st.text_area("4. UYGULAMA", value=current.get('icerik', ''))
            if st.form_submit_button("💾 DÖKÜMANI GÜNCELLE"):
                res = belge_guncelle(engine, row['belge_kodu'], new_ad, current['alt_kategori'], "", amac=e_ama, icerik=e_ice)
                if res['basarili']: 
                    st.success("Güncellendi."); st.rerun()

if __name__ == "__main__":
    qdms_main_page()
