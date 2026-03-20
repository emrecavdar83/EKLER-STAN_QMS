# pages/qdms_ana_sayfa.py
import streamlit as st
import pandas as pd
import qrcode
from io import BytesIO
import json
from database.connection import get_engine
from modules.qdms.belge_kayit import belge_olustur, belge_listele, belge_durum_guncelle
from modules.qdms.revizyon import revizyon_gecmisi_getir, revizyon_baslat
from modules.qdms.pdf_uretici import pdf_uret
from modules.qdms.sablon_motor import sablon_getir, sablon_kaydet, VARSAYILAN_HEADER_CONFIG, VARSAYILAN_KOLON_CONFIG_SOGUK_ODA
from modules.qdms.talimat_yonetici import talimat_olustur, okunmayan_talimatlar, okuma_onay_kaydet
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
        tip_filter = st.selectbox("Belge Tipi", ["Tümü", "SO", "TL", "PR", "KYS", "UR", "HACCP"], key="dm_tip")
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
                    veri = {
                        'belge_adi': row['belge_adi'],
                        'yonu': sablon.get('sayfa_yonu', 'dikey') if sablon else 'dikey',
                        'sablon': sablon,
                        'satirlar': []
                    }
                    pdf_path = pdf_uret(engine, row['belge_kodu'], veri)
                    with open(pdf_path, "rb") as f:
                        st.download_button("📥 İndir", f, file_name=f"{row['belge_kodu']}.pdf")
            else:
                c4.write("—")
                
            with c5.expander("🕒 Geçmiş"):
                history = revizyon_gecmisi_getir(engine, row['belge_kodu'])
                if not history:
                    st.write("İlk revizyon.")
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
            kod = c1.text_input("Belge Kodu", placeholder="EKL-TIP-NNN")
            ad = c1.text_input("Belge Adı")
            tip = c2.selectbox("Belge Tipi", ["SO", "TL", "PR", "KYS", "UR", "HACCP"])
            kat = c2.text_input("Alt Kategori", value="Genel")
            aciklama = st.text_area("Açıklama")
            submit = st.form_submit_button("Belgeyi Kaydet")
            if submit:
                res = belge_olustur(engine, kod, ad, tip, kat, aciklama, 1)
                if res['basarili']:
                    st.success(f"Belge oluşturuldu: {kod}")
                    sablon_kaydet(engine, kod, 1, VARSAYILAN_HEADER_CONFIG, VARSAYILAN_KOLON_CONFIG_SOGUK_ODA, {"taraf": "Kalite"})
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
