# pages/qdms_ana_sayfa.py
import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import json
from database.connection import get_engine
from modules.qdms.belge_kayit import belge_olustur, belge_listele, belge_durum_guncelle, belge_getir, belge_guncelle
from modules.qdms.revizyon import revizyon_gecmisi_getir, revizyon_baslat
from modules.qdms.pdf_uretici import pdf_uret
from modules.qdms.sablon_motor import sablon_getir, sablon_kaydet, sablon_guncelle, VARSAYILAN_HEADER_CONFIG, VARSAYILAN_KOLON_CONFIG_SOGUK_ODA
from modules.qdms.talimat_yonetici import talimat_olustur, talimat_guncelle, talimat_getir_by_kod, okunmayan_talimatlar, okuma_onay_kaydet
from modules.qdms.uyumluluk_rapor import uyumluluk_ozeti_getir
from logic.zone_yetki import eylem_yapabilir_mi

# --- ALT MODÜL İÇERİKLERİ (KONSOLİDE) ---

def qdms_dokuman_merkezi_content(engine=None):
    """Tüm personelin aktif belgelere ulaştığı merkezi alan."""
    if not engine: engine = get_engine()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        search = st.text_input("🔍 Belge Ara", "", key="dm_search")
    with col2:
        tip_filter = st.selectbox("Belge Tipi", ["Tümü", "GK", "SO", "TL", "PR", "KYS", "UR", "HACCP", "FR", "PL", "GT", "LS", "KL", "YD", "SOP"], key="dm_tip")
    with col3:
        durum_filter = st.selectbox("Durum", ["Tümü", "aktif", "taslak", "incelemede", "arsiv"], key="dm_durum")
        
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
            c1, c2, c3, c4, c5 = st.columns([2, 4, 1, 1, 2])
            c1.markdown(f"**{row['belge_kodu']}**")
            c1.caption(f"Rev: {row['aktif_rev']}")
            
            c2.markdown(f"### {row['belge_adi']}")
            c2.caption(f"Tip: {row['belge_tipi']} | Kat: {row['alt_kategori']}")
            
            colors = {"aktif": "green", "taslak": "gray", "incelemede": "orange", "arsiv": "red"}
            color = colors.get(row['durum'], "gray")
            c3.markdown(f":{color}[{row['durum'].upper()}]")
            
            if row['durum'] == 'aktif':
                if c4.button("📄 PDF", key=f"pdf_{row['belge_kodu']}"):
                    sablon = sablon_getir(engine, row['belge_kodu'])
                    # v3.4: Tüm hücreleri PDF'e gönder
                    veri = {
                        'belge_adi': row['belge_adi'], 
                        'yonu': sablon.get('sayfa_yonu', 'dikey') if sablon else 'dikey', 
                        'sablon': sablon, 
                        'satirlar': [],
                        'amac': row.get('amac', ''),
                        'kapsam': row.get('kapsam', ''),
                        'tanimlar': row.get('tanimlar', ''),
                        'dokumanlar': row.get('dokumanlar', ''),
                        'icerik': row.get('icerik', ''),
                        'belge_tipi': row['belge_tipi'],
                        'rev_no': f"{row['aktif_rev']:02d}"
                    }
                    # GK ise ek verileri çek
                    if row['belge_tipi'] == 'GK':
                        from modules.qdms.gk_logic import gk_getir
                        gk_data = gk_getir(engine, row['belge_kodu'])
                        if gk_data: veri.update(gk_data)

                    pdf_path = pdf_uret(engine, row['belge_kodu'], veri)
                    with open(pdf_path, "rb") as f:
                        st.download_button("📥 İndir", f, file_name=f"{row['belge_kodu']}.pdf", key=f"dl_{row['belge_kodu']}")
            else:
                c4.write("—")
                
            # v3.3.0: İncele ve Düzenle (ANAYASA m.5)
            with c5:
                # 👁️ İNCELE (Herkes Görebilir)
                if st.button("👁️ İncele", key=f"iv_{row['belge_kodu']}", use_container_width=True):
                    _render_belge_preview(engine, row)
                    
                # 📝 DÜZENLE (Sadece Taslak or Admin)
                can_edit = (row['durum'] == 'taslak') or (st.session_state.get('user_rol') == 'ADMIN')
                if can_edit:
                    if st.button("📝 Düzenle", key=f"ed_{row['belge_kodu']}", use_container_width=True):
                        # Tekil edit mantığı: Mevcut açıksa kapat, kapalıysa aç
                        if st.session_state.get('active_edit_bk') == row['belge_kodu']:
                            st.session_state['active_edit_bk'] = None
                        else:
                            st.session_state['active_edit_bk'] = row['belge_kodu']
                        st.rerun()
                
                if st.session_state.get('active_edit_bk') == row['belge_kodu']:
                    _render_belge_editor(engine, row)

                with st.expander("🕒 Geçmiş"):
                    history = revizyon_gecmisi_getir(engine, row['belge_kodu'])
                    if not history: st.write("İlk revizyon.")
                    for h in history:
                        st.markdown(f"**Rev {h['yeni_rev']}:** {h['degisiklik_notu']}")
                        st.caption(f"{h['degisiklik_tarihi']}")

def qdms_belge_yonetimi_content(engine=None):
    """Doküman hayat döngüsünü yöneten yönetici arayüzü."""
    if not engine: engine = get_engine()
    tab1, tab2 = st.tabs(["🆕 Yeni Kayıt", "🔄 Durum & Revizyon"])
    
    with tab1:
        with st.form("yeni_belge_form"):
            c1, c2 = st.columns(2)
            kod = c1.text_input("Belge Kodu", placeholder="GK için: EKL-KYS-GK-POZISYON-001")
            ad = c1.text_input("Belge Adı")
            tip = c2.selectbox("Belge Tipi", ["SO", "TL", "PR", "KYS", "UR", "HACCP", "FR", "PL", "GT", "LS", "KL", "YD", "GK"])
            kat = c2.text_input("Alt Kategori", value="İnsan Kaynakları")
            aciklama = st.text_area("Açıklama")
            submit = st.form_submit_button("Belgeyi Kaydet")
            if submit:
                # v3.4: Yapılandırılmış Kayıt
                kod_temiz = str(kod).upper().strip()
                res = belge_olustur(engine, kod_temiz, ad, tip, kat, aciklama, 1) # Note: icerik/amac etc will be added via Editor or expanded here if needed
                if res['basarili']:
                    st.success(f"Belge taslağı oluşturuldu: {kod_temiz}. Lütfen 'Doküman Merkezi'nden içeriği (Amaç, Kapsam vb.) düzenleyin.")
                    sablon_kaydet(engine, kod_temiz, 1, VARSAYILAN_HEADER_CONFIG, VARSAYILAN_KOLON_CONFIG_SOGUK_ODA, {"taraf": "Kalite"})
                else:
                    st.error(f"Hata: {res['hata']}")
                    
    with tab2:
        belgeler = belge_listele(engine)
        if not belgeler:
            st.warning("Henüz hiç belge yok.")
        else:
            sel_kod = st.selectbox("Belge Seç", [b['belge_kodu'] for b in belgeler], key="by_sel_kod")
            belge = next(b for b in belgeler if b['belge_kodu'] == sel_kod)
            st.divider()
            st.markdown(f"**Mevcut Durum**: :{'green' if belge['durum'] == 'aktif' else 'orange'}[{belge['durum'].upper()}]")
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Durum Değiştir")
                yeni_durum = st.selectbox("Yeni Durum", ["taslak", "incelemede", "aktif", "arsiv"])
                if st.button("Durumu Güncelle"):
                    res = belge_durum_guncelle(engine, sel_kod, yeni_durum, 1)
                    if res['basarili']:
                        st.success("Durum güncellendi.")
                        st.rerun()
                    else:
                        st.error(res['hata'])
            with c2:
                st.subheader("⚠️ Yeni Revizyon Başlat (T2)")
                st.warning("Bu işlem geri döndürülemez ve mevcut belgeyi TASLAK durumuna çeker.")
                rev_not = st.text_area("Değişiklik Notu (Zorunlu)")
                onay = st.checkbox("Bu işlemin sorumluluğunu alıyorum.", key="rev_onay")
                if st.button("Revizyon Başlat"):
                    # Katman 3: Eylem yetki kontrolü
                    if not eylem_yapabilir_mi('qdms', 'revizyon_baslat'):
                        st.error("🚫 Revizyon başlatma yetkiniz bulunmamaktadır. (Kalite/Admin)")
                    elif not onay: 
                        st.error("T2 İşlemi onaylamanız gerekmektedir.")
                    else:
                        res = revizyon_baslat(engine, sel_kod, rev_not, 1, onay_verildi=True)
                        if res['basarili']:
                            st.success(f"Yeni revizyon (v{res['yeni_rev']}) başlatıldı.")
                            st.rerun()
                        else: st.error(res['hata'])

def qdms_talimat_content(engine=None):
    """Talimat (SOP) yönetimi ve QR kod üretimi."""
    if not engine: engine = get_engine()
    tab1, tab2, tab3 = st.tabs(["🆕 Yeni Talimat", "📜 Onay Bekleyenler", "🔍 Talimat Ara"])
    
    with tab1:
        st.subheader("Talimat Oluştur")
        with st.form("yeni_talimat_form"):
            c1, c2 = st.columns(2)
            tk = c1.text_input("Talimat Kodu (EKL-TL-NNN)")
            ta = c1.text_input("Talimat Adı")
            tt = c2.selectbox("Tipi", ["Hijyen", "Makine Kullanım", "Bakım", "Güvenlik"])
            dep = c2.text_input("Departman", value="Üretim")
            st.write("---")
            st.write("Adımlar (JSON Formatında)")
            adimlar_text = st.text_area("Örn: [{\"sira\": 1, \"baslik\": \"Giriş\", \"aciklama\": \"...\"}]", value="[]")
            submit = st.form_submit_button("Talimatı Kaydet")
            if submit:
                try:
                    adimlar = json.loads(adimlar_text)
                    res = talimat_olustur(engine, tk, ta, tt, adimlar, departman=dep)
                    if res['basarili']:
                        st.success(f"Talimat oluşturuldu. Token: {res['qr_token']}")
                        qr = qrcode.QRCode(version=1, box_size=10, border=5)
                        qr.add_data(res['qr_token'])
                        qr.make(fit=True)
                        img = qr.make_image(fill='black', back_color='white')
                        buf = BytesIO()
                        img.save(buf)
                        st.image(buf.getvalue(), caption=f"{tk} için QR Kod")
                    else: st.error(res['hata'])
                except Exception as e: st.error(f"Geçersiz JSON: {e}")
                    
    with tab2:
        st.subheader("Okuma Onayı Bekleyenler")
        pid = st.number_input("Personel ID (Simülasyon)", value=1, step=1)
        bekleyen = okunmayan_talimatlar(engine, pid)
        if not bekleyen: st.success("Tüm talimatlar okunmuş! 🎉")
        else:
            for t in bekleyen:
                with st.expander(f"{t['talimat_kodu']} — {t['talimat_adi']}"):
                    st.write(f"Tip: {t['talimat_tipi']} | Dep: {t['departman']}")
                    if st.button("Okudum, Anladım ve Onaylıyorum", key=f"onay_{t['talimat_kodu']}"):
                        res = okuma_onay_kaydet(engine, t['talimat_kodu'], 1, pid)
                        if res['basarili']: st.rerun()
    with tab3: st.info("Arama ve tüm talimat listesi geliştirme aşamasındadır.")

def qdms_uyumluluk_content(engine=None):
    """BRCGS/IFS standartlarına göre kalite puanlaması ve raporlama."""
    if not engine: engine = get_engine()
    ozet = uyumluluk_ozeti_getir(engine)
    if "hata" in ozet:
        st.error(f"Veri çekme hatası: {ozet['hata']}")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Aktif Belgeler", ozet['aktif_belge_sayisi'])
    c2.metric("Taslak Sayısı", ozet['taslak_sayisi'])
    c3.metric("Arşiv Belgesi", ozet['arsiv_sayisi'])
    c4.metric("Son 30G Rev.", ozet['son_30_gun_revizyon'])
    st.markdown("---")
    st.subheader("BRC Uyum Skoru")
    skor = ozet['brc_uyum_skoru']
    st.progress(skor / 100.0)
    if skor >= 75: st.success(f"Mevcut Skor: {skor}/100 — Sistem Uyumlu.")
    elif skor >= 50: st.warning(f"Mevcut Skor: {skor}/100 — İyileştirme Gerekli.")
    else: st.error(f"Mevcut Skor: {skor}/100 — Kritik Risk!")
    st.markdown("---")
    st.subheader("🕒 Güncelliğini Yitirmekte Olan Belgeler (12 Ay+)")
    if not ozet['eskiyen_belgeler']: st.success("Tüm belgeler güncel.")
    else:
        df_eski = pd.DataFrame(ozet['eskiyen_belgeler'])
        st.table(df_eski)
    st.sidebar.markdown("### Denetim Araçları")
    if st.sidebar.button("📊 Denetim Export (CSV)"):
        full_data = pd.DataFrame([ozet])
        csv = full_data.to_csv(index=False).encode('utf-8')
        st.sidebar.download_button(label="📥 Raporu İndir", data=csv, file_name=f"ekleristan_qdms_audit_{pd.Timestamp.now().date()}.csv", mime="text/csv")

# --- ANA SAYFA MANTIĞI ---

def qdms_main_page(engine=None):
    # st.set_page_config kaldırıldı (app.py tarafından yönetiliyor)
    st.title("📁 QDMS - Kalite Doküman Yönetim Sistemi")
    
    user_rol = st.session_state.get('user_rol', 'Personel')
    can_manage = user_rol.upper() in ['ADMIN', 'KALİTE', 'MÜDÜRLER', 'DİREKTÖRLER']
    can_view_audit = user_rol.upper() in ['ADMIN', 'KALİTE', 'MÜDÜRLER', 'DİREKTÖRLER', 'YÖNETİM KURULU', 'GENEL MÜDÜR']
    
    tabs_config = [
        ("📋 Doküman Merkezi", lambda: qdms_dokuman_merkezi_content(engine), True),
        ("⚙️ Belge Yönetimi",  lambda: qdms_belge_yonetimi_content(engine),  can_manage),
        ("📖 Talimatlar",      lambda: qdms_talimat_content(engine),         True),
        ("📊 Uyumluluk Panosu",lambda: qdms_uyumluluk_content(engine),      can_view_audit),
    ]
    
    visible = [(lbl, fn) for lbl, fn, cond in tabs_config if cond]
    if not visible:
        st.warning("Erişim yetkiniz olan bir QDMS bölümü bulunamadı.")
        return

    tabs = st.tabs([lbl for lbl, _ in visible])
    for tab, (_, fn) in zip(tabs, visible):
        with tab:
            fn()

if __name__ == "__main__":
    qdms_main_page()


# --- YARDIMCI GÖRÜNÜM BİLEŞENLERİ (EDITÖR & PREVIEW) ---

@st.dialog("👁️ Belge Önizleme", width="large")
def _render_belge_preview(engine, row):
    # GK Özel Önizleme
    is_gk = row['belge_tipi'] == 'GK' or '-GK-' in row['belge_kodu']
    if is_gk:
        from modules.qdms.gk_logic import gk_getir
        gk = gk_getir(engine, row['belge_kodu'])
        if gk:
            st.markdown("### 📋 Pozisyon Profili")
            c1, c2 = st.columns(2)
            c1.write(f"**Departman:** {gk['departman']}")
            c1.write(f"**Bağlı Pozisyon:** {gk['bagli_pozisyon']}")
            c2.write(f"**Zone:** {gk['zone'].upper()}")
            c2.write(f"**Çalışma Düzeni:** {gk['vardiya_turu']}")
            
            st.markdown("### 🎯 3. Görev Özeti")
            st.info(gk['gorev_ozeti'] or "-")
            
            st.markdown("### 🛡️ 4. Sorumluluk Alanları")
            for s in gk['sorumluluklar']:
                st.write(f"- [{s['kategori'].upper()}] {s['sorumluluk']}")
            
            st.divider()
            st.markdown("### ⚖️ 5. Yetki & 8. Nitelik")
            c3, c4 = st.columns(2)
            c3.write(f"**Finansal Yetki:** {gk.get('finansal_yetki_tl','0')} TL")
            c3.write(f"**İmza Yetkisi:** {gk.get('imza_yetkisi','-')}")
            c4.write(f"**Eğitim:** {gk.get('min_egitim','-')}")
            c4.write(f"**Deneyim:** {gk.get('min_deneyim_yil','0')} yıl")
            
            st.markdown("### 🤝 6. Süreçler Arası Etkileşim (RACI)")
            if gk.get('etkilesimler'):
                df_e = pd.DataFrame(gk['etkilesimler'])[['taraf', 'konu', 'raci_rol']]
                st.table(df_e)
            else: st.caption("- Etkileşim tanımlanmamış -")

            st.markdown("### 📅 7. Periyodik Görev Listesi")
            if gk.get('periyodik_gorevler'):
                st.table(pd.DataFrame(gk['periyodik_gorevler'])[['gorev_adi', 'periyot']])
            else: st.caption("- Görev tanımlanmamış -")

            st.markdown("### 📊 9. Performans Göstergeleri (KPI)")
            if gk.get('kpi_listesi'):
                st.table(pd.DataFrame(gk['kpi_listesi'])[['kpi_adi', 'olcum_birimi', 'hedef_deger']])
            else: st.caption("- KPI tanımlanmamış -")
        return

    # BRC/IFS Hücreleri (SOP/PR vb için)
    cols = st.columns(2)
    with cols[0]:
        st.markdown("### 🎯 1. AMAÇ")
        st.write(row.get('amac', 'Tanımlanmamış'))
        st.markdown("### 📚 3. TANIMLAR")
        st.write(row.get('tanimlar', 'Tanımlanmamış'))
    with cols[1]:
        st.markdown("### 🌐 2. KAPSAM")
        st.write(row.get('kapsam', 'Tanımlanmamış'))
        st.markdown("### 🔗 5. İLGİLİ DOKÜMANLAR")
        st.write(row.get('dokumanlar', 'Tanımlanmamış'))
    
    st.divider()
    st.markdown("### 📝 4. UYGULAMA (İÇERİK)")
    if row.get('icerik'):
        st.info(row['icerik'])
    
    # Talimat Adımları
    talimat = talimat_getir_by_kod(engine, row['belge_kodu'])
    if talimat:
        st.write("#### 📜 Uygulama Adımları (SOP)")
        try:
            adimlar = json.loads(talimat['adimlar_json'])
            for a in adimlar:
                st.write(f"**{a['sira']}. {a['baslik']}**: {a['aciklama']}")
        except: st.error("Adımlar yüklenemedi.")
    
    # Sablon (Kolonlar)
    sablon = sablon_getir(engine, row['belge_kodu'])
    if sablon:
        st.write("#### 📋 Kayıt Tablosu Yapısı")
        k_df = pd.DataFrame(sablon['kolon_config'])
        st.table(k_df[['ad', 'tip', 'genislik_yuzde']])

def _render_gk_profil_editor(gk, row):
    """Bölüm 2 & 3: Profil ve Özet."""
    st.subheader("2. Pozisyon Profili & 3. Görev Özeti")
    c1, c2 = st.columns(2)
    p_ad = c1.text_input("Pozisyon Adı", value=gk.get('pozisyon_adi', row['belge_adi']))
    dep  = c2.text_input("Departman", value=gk.get('departman', ''))
    bp   = c1.text_input("Bağlı Pozisyon", value=gk.get('bagli_pozisyon', ''))
    ve   = c2.text_input("Vekâlet Eden", value=gk.get('vekalet_eden', ''))
    zn   = c1.selectbox("Zone", ["mgt", "ops", "sys"], index=0)
    vt   = c2.text_input("Vardiya", value=gk.get('vardiya_turu',''))
    g_ozet = st.text_area("Genel Görev Amacı", value=gk.get('gorev_ozeti',''))
    return {"pa": p_ad, "dep": dep, "bp": bp, "ve": ve, "zn": zn, "vt": vt, "go": g_ozet}

def _render_disiplin_editor(gk, d_tip, label):
    """Bölüm 4: Tek bir disiplin tab içeriği (Anayasa m.5)."""
    st.markdown(f"**{label}**")
    existing = [s for s in gk.get('sorumluluklar', []) if s.get('disiplin_tipi') == d_tip]
    s_text = "\n".join([s['sorumluluk'] for s in existing])
    
    # Etkilesim Birimleri (Multiselect)
    depts = ["İK", "Kalite", "Operasyon", "Finans", "Satın Alma", "Bakım", "IT", "Yönetim", "Lojistik", "Satış", "Pazarlama"]
    current_units = []
    for s in existing:
        if s.get('etkilesim_birimleri'):
            current_units.extend([u.strip() for u in s['etkilesim_birimleri'].split(',') if u.strip() in depts])
    
    res_text = st.text_area(f"Sorumluluklar ({label})", value=s_text, height=120, key=f"gk_sor_{d_tip}")
    res_units = st.multiselect("Etkileşim Halindeki Birimler (RACI)", depts, default=list(set(current_units)), key=f"gk_uni_{d_tip}")
    return res_text, res_units

def _render_gk_sorumluluklar_editor(gk):
    """Bölüm 4: 5 Disiplinli Tab Yapısı (st.tabs)."""
    st.subheader("4. Sorumluluk Alanları (Disiplinler)")
    t_names = ["👥 Personel", "⚙️ Operasyon", "🛡️ Gıda/Kalite", "👷 İSG", "🌱 Çevre"]
    tabs = st.tabs(t_names)
    
    t_per, t_uni_per = None, None
    with tabs[0]: t_per, t_uni_per = _render_disiplin_editor(gk, 'personel', 'Personel Yönetimi Sorumlulukları')
    with tabs[1]: t_ops, t_uni_ops = _render_disiplin_editor(gk, 'operasyon', 'Operasyonel Gereklilikler')
    with tabs[2]: t_gg, t_uni_gg = _render_disiplin_editor(gk, 'gida_guvenligi', 'Gıda Güvenliği & Kalite')
    with tabs[3]: t_isg, t_uni_isg = _render_disiplin_editor(gk, 'isg', 'İSG Sorumlulukları')
    with tabs[4]: t_cev, t_uni_cev = _render_disiplin_editor(gk, 'cevre', 'Çevre Gereklilikleri')
    
    return {
        'personel': (t_per, t_uni_per), 'operasyon': (t_ops, t_uni_ops),
        'gida_guvenligi': (t_gg, t_uni_gg), 'isg': (t_isg, t_uni_isg), 'cevre': (t_cev, t_uni_cev)
    }

def _render_gk_yetki_nitelik_editor(gk):
    """Bölüm 5 & 8: Yetki ve Nitelikler."""
    st.divider()
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("5. Yetki Sınırları")
        fy = st.text_input("Finansal Yetki (TL)", value=gk.get('finansal_yetki_tl','0'))
        iy = st.text_input("İmza Yetkisi", value=gk.get('imza_yetkisi',''))
        vk = st.text_area("Vekâlet Devir Koşulları", value=gk.get('vekalet_kosullari',''), height=70)
    with c4:
        st.subheader("8. Nitelik ve Yetkinlik")
        me = st.text_input("Eğitim Gereksinimi", value=gk.get('min_egitim',''))
        md = st.number_input("Min. Deneyim (Yıl)", value=int(gk.get('min_deneyim_yil', 0)))
        tn = st.text_area("Tercihli Nitelikler", value=gk.get('tercihli_nitelikler',''), height=70)
    return {"fy": fy, "iy": iy, "vk": vk, "me": me, "md": md, "tn": tn}

def _render_gk_alt_bolum_editor(gk):
    """Bölüm 6, 7 & 9: Alt Tablolar (RACI, Görevler, KPI)."""
    st.subheader("6-7-9. Alt Detaylar (RACI, Görev, KPI)")
    e_txt = st.text_area("6. Etkileşim Listesi (Taraf | Konu | Yöntem | RACI)", value="\n".join([f"{e['taraf']} | {e['konu']} | {e.get('siklik','-')} | {e['raci_rol']}" for e in gk.get('etkilesimler', [])]), height=80)
    p_txt = st.text_area("7. Periyodik Görevler (Görev | Periyot | Madde)", value="\n".join([f"{g['gorev_adi']} | {g['periyot']} | {g.get('sertifikasyon_maddesi','')}" for g in gk.get('periyodik_gorevler', [])]), height=80)
    k_txt = st.text_area("9. KPI Listesi (KPI Adı | Birim | Hedef)", value="\n".join([f"{k['kpi_adi']} | {k['olcum_birimi']} | {k['hedef_deger']}" for k in gk.get('kpi_listesi', [])]), height=80)
    return {"e": e_txt, "p": p_txt, "k": k_txt}

def _handle_gk_save(engine, bk, p, s, y, a):
    """GK verilerini toplar ve kaydeder (Anayasa m.5)."""
    from modules.qdms.gk_logic import gk_kaydet
    
    # Sorumluluklari ayristir (v3.6: 5-Discipline + Inter-Units)
    sor_list = []
    for d_tip, (text_val, units) in s.items():
        eb_str = ",".join(units)
        for i, line in enumerate(text_val.split("\n")):
            if line.strip(): 
                sor_list.append({
                    "disiplin_tipi": d_tip, 
                    "kategori": d_tip.replace('_', ' ').title(), # Simple title for category
                    "sira_no": i+1, 
                    "sorumluluk": line.strip(),
                    "etkilesim_birimleri": eb_str
                })
    
    # 6. Etkilesimleri ayristir
    etk_list = []
    for l in a['e'].split("\n"):
        if not l.strip(): continue
        parts = [x.strip() for x in l.split('|')]
        if len(parts) >= 4: etk_list.append({"taraf": parts[0], "konu": parts[1], "siklik": parts[2], "raci_rol": parts[3]})
        elif len(parts) == 3: etk_list.append({"taraf": parts[0], "konu": parts[1], "siklik": "-", "raci_rol": parts[2]})
        elif len(parts) == 2: etk_list.append({"taraf": parts[0], "konu": parts[1], "siklik": "-", "raci_rol": "-"})
        else: etk_list.append({"taraf": "Genel", "konu": l.strip(), "siklik": "-", "raci_rol": "-"})
    
    # 7. Periyodik Gorevler
    per_list = []
    for l in a['p'].split("\n"):
        if not l.strip(): continue
        parts = [x.strip() for x in l.split('|')]
        if len(parts) >= 3: per_list.append({"gorev_adi": parts[0], "periyot": parts[1], "sertifikasyon_maddesi": parts[2]})
        elif len(parts) == 2: per_list.append({"gorev_adi": parts[0], "periyot": parts[1], "sertifikasyon_maddesi": "-"})
        else: per_list.append({"gorev_adi": l.strip(), "periyot": "-", "sertifikasyon_maddesi": "-"})

    # 9. KPI
    kpi_list = []
    for l in a['k'].split("\n"):
        if not l.strip(): continue
        parts = [x.strip() for x in l.split('|')]
        if len(parts) >= 3: kpi_list.append({"kpi_adi": parts[0], "olcum_birimi": parts[1], "hedef_deger": parts[2], "degerlendirme_periyodu": "Aylık", "degerlendirici": "Yönetim"})
        elif len(parts) == 2: kpi_list.append({"kpi_adi": parts[0], "olcum_birimi": parts[1], "hedef_deger": "-", "degerlendirme_periyodu": "Aylık", "degerlendirici": "Yönetim"})
        else: kpi_list.append({"kpi_adi": l.strip(), "olcum_birimi": "-", "hedef_deger": "-", "degerlendirme_periyodu": "Aylık", "degerlendirici": "Yönetim"})

    gk_data = {
        'belge_kodu': bk, 'pozisyon_adi': p['pa'], 'departman': p['dep'],
        'bagli_pozisyon': p['bp'], 'vekalet_eden': p['ve'], 'zone': p['zn'], 'vardiya_turu': p['vt'],
        'gorev_ozeti': p['go'], 'min_egitim': y['me'], 'min_deneyim_yil': y['md'],
        'finansal_yetki_tl': y['fy'], 'imza_yetkisi': y['iy'], 'vekalet_kosullari': y['vk'],
        'tercihli_nitelikler': y['tn'], 'olusturan_id': 1, # TODO: Dinamik olusturan_id
        'sorumluluklar': sor_list, 'etkilesimler': etk_list, 
        'periyodik_gorevler': per_list, 'kpi_listesi': kpi_list
    }
    res = gk_kaydet(engine, gk_data)
    if res['basarili']: st.success("Görev Kartı 10 bölüm olarak başarıyla güncellendi."); st.rerun()
    else: st.error(res['hata'])

def _render_standard_editor(engine, row):
    """Standart belge editörünü (PR/TL/SO) render eder."""
    current_belge = belge_getir(engine, row['belge_kodu'])
            k_text = st.text_area("KPI Listesi", value=existing_kpi, height=100)

def _handle_gk_save(engine, bk, p, s, y, a):
    """GK verilerini toplar ve kaydeder (v3.6: 5-Discipline)."""
    from modules.qdms.gk_logic import gk_kaydet
    sor_list = []
    for d_tip, (text_val, units) in s.items():
        eb_str = ", ".join(units)
        for i, line in enumerate(text_val.split("\n")):
            if line.strip(): sor_list.append({"disiplin_tipi": d_tip, "sira_no": i+1, "sorumluluk": line.strip(), "etkilesim_birimleri": eb_str})
    
    # Alt Tablo Parsers
    etk_list = [{"taraf": x.split('|')[0].strip(), "konu": x.split('|')[1].strip(), "siklik": x.split('|')[2].strip() if len(x.split('|'))>2 else "-", "raci_rol": x.split('|')[3].strip() if len(x.split('|'))>3 else "-"} for x in a['e'].split("\n") if '|' in x]
    per_list = [{"gorev_adi": x.split('|')[0].strip(), "periyot": x.split('|')[1].strip(), "sertifikasyon_maddesi": x.split('|')[2].strip() if len(x.split('|'))>2 else ""} for x in a['p'].split("\n") if '|' in x]
    kpi_list = [{"kpi_adi": x.split('|')[0].strip(), "olcum_birimi": x.split('|')[1].strip(), "hedef_deger": x.split('|')[2].strip() if len(x.split('|'))>2 else "", "degerlendirme_periyodu": "Aylık", "degerlendirici": "Yönetim"} for x in a['k'].split("\n") if '|' in x]

    gk_data = {
        'belge_kodu': bk, 'pozisyon_adi': p['pa'], 'departman': p['dep'], 'bagli_pozisyon': p['bp'], 'vekalet_eden': p['ve'], 'zone': p['zn'], 'vardiya_turu': p['vt'], 'gorev_ozeti': p['go'],
        'min_egitim': y['me'], 'min_deneyim_yil': y['md'], 'finansal_yetki_tl': y['fy'], 'imza_yetkisi': y['iy'], 'vekalet_kosullari': y['vk'], 'tercihli_nitelikler': y['tn'], 'olusturan_id': 1,
        'sorumluluklar': sor_list, 'etkilesimler': etk_list, 'periyodik_gorevler': per_list, 'kpi_listesi': kpi_list
    }
    res = gk_kaydet(engine, gk_data)
    if res['basarili']: st.success("Görev Kartı başarıyla güncellendi."); st.rerun()
    else: st.error(res['hata'])

def _render_standard_editor(engine, row):
    """Standart Belge Editörü (SOP/PR vb.) - Anayasa m.5."""
    current_belge = belge_getir(engine, row['belge_kodu'])
    with st.form(f"edit_form_{row['belge_kodu']}"):
        c1, c2 = st.columns(2)
        new_ad = c1.text_input("Belge Adı", value=current_belge['belge_adi'])
        new_kat = c2.text_input("Alt Kategori", value=current_belge['alt_kategori'])
        e_amac = st.text_area("1. AMAÇ", value=current_belge.get('amac', ''), height=80)
        e_kapsam = st.text_area("2. KAPSAM", value=current_belge.get('kapsam', ''), height=80)
        e_tanimlar = st.text_area("3. TANIMLAR", value=current_belge.get('tanimlar', ''), height=80)
        e_icerik = st.text_area("4. UYGULAMA", value=current_belge.get('icerik', ''), height=150)
        e_dokumanlar = st.text_area("5. İLGİLİ DOKÜMANLAR", value=current_belge.get('dokumanlar', ''), height=80)
        if st.form_submit_button("💾 KAYDET"):
            res = belge_guncelle(engine, row['belge_kodu'], new_ad, new_kat, current_belge['aciklama'], amac=e_amac, kapsam=e_kapsam, tanimlar=e_tanimlar, dokumanlar=e_dokumanlar, icerik=e_icerik)
            if res['basarili']: st.success("Belge güncellendi."); st.rerun()
            else: st.error(res['hata'])
        
        # Talimat Adımları
        talimat = talimat_getir_by_kod(engine, row['belge_kodu'])
        adimlar_json = talimat['adimlar_json'] if talimat else "[]"
        if talimat:
            st.info("💡 Bu bir Talimat (SOP). Aşağıdaki JSON alanından adımları profesyonelce düzenleyebilirsiniz.")
            adimlar_json = st.text_area("Adımlar (Kod)", value=talimat['adimlar_json'], height=150)

        if st.form_submit_button("💾 TÜM İÇERİĞİ KAYDET"):
            # 1. Belgeler Tablosu Guncelleme
            res1 = belge_guncelle(engine, row['belge_kodu'], new_ad, new_kat, e_aciklama, 
                                  amac=e_amac, kapsam=e_kapsam, tanimlar=e_tanimlar, 
                                  dokumanlar=e_dokumanlar, icerik=e_icerik)
            
            # 2. Talimat Tablosu Guncelleme
            res2 = {"basarili": True}
            if talimat:
                try: 
                    new_adimlar = json.loads(adimlar_json)
                    res2 = talimat_guncelle(engine, row['belge_kodu'], new_adimlar)
                except: res2 = {"basarili": False, "hata": "Adımlar geçersiz JSON formatında!"}
                
            if res1['basarili'] and res2['basarili']:
                st.success("Tebrikler! Belge BRC/IFS standartlarına uygun olarak güncellendi.")
                st.rerun()
            else:
                st.error(f"Hata Oluştu: {res1.get('hata','')}{res2.get('hata','')}")
