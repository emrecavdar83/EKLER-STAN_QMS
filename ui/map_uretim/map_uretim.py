import streamlit as st
import pandas as pd
from datetime import datetime
import pytz, time

from database.connection import get_engine
from . import map_db as db
from . import map_hesap as hesap
from logic.auth_logic import kullanici_yetkisi_var_mi

# ─── Config (Anayasa: Zero Hardcode) ─────────────────────────────────────────
MAP_MAKINA_LISTESI = ["MAP-01", "MAP-02", "MAP-03"]
MAP_DURUS_NEDENLERI = [
    "ÜST FİLM DEĞİŞİMİ", "ALT FİLM DEĞİŞİMİ", "MOLA / YEMEK",
    "ARIZA / BAKIM", "SETUP / AYAR", "ÜRETM BEKLEME",
    "TEMİZLİK / SANİTASYON", "DİĞER",
]
MAP_FIRE_TIPLERI = [
    "Bobin Başı Fire", "Bobin Sonu Fire", "Film Değişimi Fire",
    "Sızdırmazlık / Kaçak", "Yırtık / Delik Film", "Gaz Hatası",
    "Besleme Hatası", "Operatör Hatası", "Diğer",
]
_TZ = pytz.timezone("Europe/Istanbul")


# ─── Session State Bootstrap ──────────────────────────────────────────────────
def _init_state():
    defaults = {
        "map_aktif_vardiya_id": None,
        "map_canli_mod": True,
        "map_son_tık_ts": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _is_click_safe():
    """13. Adam: Arka arkaya hızlı tıklama koruması (1 sn)."""
    now = time.time()
    if now - st.session_state.map_son_tık_ts < 1.0:
        return False
    st.session_state.map_son_tık_ts = now
    return True


# ─── Tab 1 — Vardiya ──────────────────────────────────────────────────────────
def _tab_vardiya(engine):
    aktif = db.get_aktif_vardiya(engine)

    if aktif is None:
        st.info("📋 Bugün açık vardiya yok. Yeni vardiya başlatın.")
        with st.form("yeni_vardiya_form"):
            c1, c2 = st.columns(2)
            makina = c1.selectbox("🏭 Makina", MAP_MAKINA_LISTESI)
            vno = c2.selectbox("⏰ Vardiya No", [1, 2, 3])
            op = st.text_input("👷 Operatör Adı (Soyadı)")
            sef = st.text_input("👔 Vardiya Şefi (boş bırakılabilir)")
            c3, c4, c5 = st.columns(3)
            bes = c3.number_input("Besleme Kişi", 0, 20, 4)
            kas = c4.number_input("Kasalama Kişi", 0, 20, 1)
            hiz = c5.number_input("🎯 Hedef Hız (pk/dk)", 0.1, 20.0, 4.2, step=0.1)
            if st.form_submit_button("🟢 VARDİYAYI BAŞLAT", use_container_width=True, type="primary"):
                if not op.strip():
                    st.error("Operatör adı zorunludur!")
                    return
                try:
                    vid = db.aç_vardiya(engine, makina, vno, op.strip(), sef.strip(),
                                        int(bes), int(kas), float(hiz))
                    db.insert_zaman_kaydi(engine, vid, "CALISIYOR")
                    st.session_state.map_aktif_vardiya_id = vid
                    st.success(f"✅ Vardiya açıldı! ID: {vid}")
                    time.sleep(0.5)
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
    else:
        st.session_state.map_aktif_vardiya_id = int(aktif['id'])
        bas = aktif['baslangic_saati']
        st.success(f"✅ **{aktif['makina_no']}** | {aktif['vardiya_no']}. Vardiya | Başlangıç: **{bas}**")
        st.caption(f"👷 Operatör: **{aktif['operator_adi']}**")

        simdi = datetime.now(_TZ)
        try:
            bas_dt = datetime.strptime(f"{aktif['tarih']} {bas}:00", "%Y-%m-%d %H:%M:%S")
        except Exception:
            bas_dt = simdi.replace(tzinfo=None)
        
        simdi_naive = simdi.replace(tzinfo=None)
        gecen = simdi_naive - bas_dt
        h, rem = divmod(int(gecen.total_seconds()), 3600)
        m, s2 = divmod(rem, 60)
        
        c1, c2 = st.columns(2)
        c1.metric("⏱️ Vardiya Süresi", f"{h:02d}:{m:02d}:{s2:02d}")
        
        uretim = c2.number_input("📦 Üretilen Paket", 0, 100000, int(aktif['gerceklesen_uretim']))
        notlar = st.text_area("📝 Vardiya Notu", value=aktif.get('notlar', '') or "")
        
        # 13. Adam: Yanlışlıkla vardiya kapatma koruması
        with st.popover("🔴 VARDİYAYI KAPAT", use_container_width=True):
            st.warning("Vardiyayı kapatmak istediğinize emin misiniz?")
            if st.button("EVET, KAPAT", use_container_width=True, type="primary"):
                db.kapat_vardiya(engine, int(aktif['id']), int(uretim))
                st.session_state.map_aktif_vardiya_id = None
                st.success("Vardiya kapatıldı!")
                time.sleep(0.5)
                st.rerun()


# ─── Tab 2 — Zaman Çizelgesi (OPERATÖR KONTROL MERKEZİ) ────────────────────
def _tab_zaman(engine, vardiya_id):
    son = db.get_son_zaman_kaydi(engine, vardiya_id)
    durum = son['durum'] if son else "CALISIYOR"
    aktif_neden = son.get('neden', '') if son else ''

    # 1. DURUM GÖSTERGESİ (BÜYÜK)
    if durum == "CALISIYOR":
        st.markdown(f'<div style="background-color:#d4edda; padding:20px; border-radius:10px; text-align:center; border:2px solid #28a745;">'
                    f'<h2 style="color:#155724; margin:0;">🟢 MAKİNA ÇALIŞIYOR</h2>'
                    f'<p style="margin:0; font-size:1.2em;">Başlangıç: {son["baslangic_ts"][11:16]}</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="background-color:#f8d7da; padding:20px; border-radius:10px; text-align:center; border:2px solid #dc3545;">'
                    f'<h2 style="color:#721c24; margin:0;">🔴 DURUŞ: {aktif_neden}</h2>'
                    f'<p style="margin:0; font-size:1.2em;">Başlangıç: {son["baslangic_ts"][11:16]}</p></div>', unsafe_allow_html=True)
    
    st.write("")

    # 2. HIZLI DURUŞ BUTONLARI (ONE-CLICK)
    if durum == "CALISIYOR":
        st.subheader("⏸️ DURUŞ BAŞLAT (Tek Tık)")
        cols = st.columns(3)
        for i, ned in enumerate(MAP_DURUS_NEDENLERI):
            if cols[i % 3].button(f"🔻 {ned}", key=f"durus_{i}", use_container_width=True):
                if _is_click_safe():
                    db.insert_zaman_kaydi(engine, vardiya_id, "DURUS", neden=ned)
                    st.rerun()
    else:
        if st.button("🟢 İŞE BAŞLA (Makina Devreye Alındı)", use_container_width=True, type="primary", key="btn_ise_basla"):
            if _is_click_safe():
                db.insert_zaman_kaydi(engine, vardiya_id, "CALISIYOR")
                st.rerun()

    st.divider()
    
    # 3. MANUEL KAYIT VE TABLO
    with st.expander("🛠️ Manuel Kayıt Ekle / Geçmişi Gör"):
        tarih = datetime.now(_TZ).strftime("%Y-%m-%d")
        with st.form("manuel_zaman_form"):
            c1, c2 = st.columns(2)
            m_bas = c1.text_input("Başlangıç (SS:DD)", placeholder="08:30")
            m_bit = c2.text_input("Bitiş (SS:DD)", placeholder="08:45")
            m_durum = st.selectbox("Durum", ["CALISIYOR", "DURUS"])
            m_neden = st.selectbox("Neden", ["-"] + MAP_DURUS_NEDENLERI)
            if st.form_submit_button("➕ MANUEL EKLE", use_container_width=True):
                if _is_click_safe():
                    try:
                        db.manuel_zaman_ekle(engine, vardiya_id, m_bas, m_bit, m_durum, 
                                            m_neden if m_neden != "-" else None, "", tarih)
                        st.success("Eklendi!"); st.rerun()
                    except Exception as e:
                        st.error(f"Hata: {e}")
        
        df = db.get_zaman_cizelgesi(engine, vardiya_id)
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
            if st.button("🗑️ Son Kaydı Sil (Hata Düzeltme)"):
                db.sil_son_zaman_kaydi(engine, vardiya_id)
                st.rerun()


# ─── Tab 3 — Bobin ───────────────────────────────────────────────────────────
def _tab_bobin(engine, vardiya_id):
    st.subheader("🎞️ Bobin Değişim Kaydı")
    if st.button("⚡ ŞİMDİ BOBİN DEĞİŞTİRDİM", use_container_width=True, type="primary"):
        st.session_state["map_bobin_form"] = True

    if st.session_state.get("map_bobin_form"):
        with st.form("bobin_form"):
            lot = st.text_input("📦 LOT / Seri No")
            c1, c2 = st.columns(2)
            bitis_m = c1.number_input("Kalan Metre (eski)", 0.0, 1000.0, 0.0)
            bas_m = c2.number_input("Yeni Bobin (m)", 0.0, 1000.0, 300.0)
            acl = st.text_input("Açıklama")
            if st.form_submit_button("💾 KAYDET"):
                db.insert_bobin(engine, vardiya_id, lot, bitis_m, acl, bas_m)
                st.session_state["map_bobin_form"] = False
                st.success("Kaydedildi!"); st.rerun()

    df = db.get_bobinler(engine, vardiya_id)
    if not df.empty:
        st.dataframe(df[['sira_no', 'degisim_ts', 'bobin_lot', 'kullanilan_m', 'aciklama']], use_container_width=True, hide_index=True)


# ─── Tab 4 — Fire ─────────────────────────────────────────────────────────────
def _tab_fire(engine, vardiya_id):
    st.subheader("🔥 Fire Kaydı")
    st.caption("Miktar girin ve fire tipine dokunun:")
    miktar = st.number_input("Miktar (adet)", 1, 1000, 1)
    
    cols = st.columns(3)
    for i, tip in enumerate(MAP_FIRE_TIPLERI):
        if cols[i % 3].button(tip, key=f"fire_btn_{i}", use_container_width=True):
            if _is_click_safe():
                db.insert_fire(engine, vardiya_id, tip, int(miktar))
                st.toast(f"✅ {miktar} adet {tip} kaydedildi!")
    
    st.divider()
    df = db.get_fire_kayitlari(engine, vardiya_id)
    if not df.empty:
        st.dataframe(df[['fire_tipi', 'miktar_adet', 'olusturma_ts']], use_container_width=True, hide_index=True)


# ─── Tab 5 — Rapor (LIVE DASHBOARD) ───────────────────────────────────────────
def _tab_rapor(engine, vardiya_id):
    st.subheader("📊 Canlı Vardiya Dashboard")
    ozet = hesap.hesapla_sure_ozeti(engine, vardiya_id)
    uretim = hesap.hesapla_uretim(engine, vardiya_id)
    
    if not ozet or not uretim:
        st.warning("Veriler hesaplanıyor..."); return

    # 1. KPI Kartları
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Üretim", f"{uretim['gerceklesen_uretim']} pk", f"Hedef: {uretim['teorik_uretim']}")
    c2.metric("OEE (Kul.)", f"%{ozet['kullanilabilirlik_pct']}")
    c3.metric("🔥 Fire", f"%{uretim['fire_pct']}", f"{uretim['fire_adet']} adet")
    c4.metric("🚀 Hız", f"{uretim['gercek_hiz']} pk/dk", f"{uretim['hiz_farki_pct']}%")

    st.divider()

    # 2. Grafikler (Plotly import yerine basit bar chart)
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.write("**⏱️ Duruş Dağılımı (dk)**")
        durus_df = pd.DataFrame(hesap.hesapla_durus_ozeti(engine, vardiya_id))
        if not durus_df.empty:
            st.bar_chart(durus_df.set_index('neden')['toplam_dk'])
        else:
            st.info("Henüz duruş kaydı yok.")

    with col_right:
        st.write("**🔥 Fire Tipleri (adet)**")
        fire_df = pd.DataFrame(hesap.hesapla_fire_ozeti(engine, vardiya_id))
        if not fire_df.empty:
            st.bar_chart(fire_df.set_index('fire_tipi')['miktar'])
        else:
            st.info("Henüz fire kaydı yok.")

    st.divider()
    
    # 3. PDF RAPORU (Anayasa m.2)
    try:
        from .map_rapor_pdf import uret_is_raporu
        if st.button("📄 VARDİYA SONU PDF RAPORU ÜRET", use_container_width=True, type="primary"):
            with st.spinner("PDF hazırlanıyor..."):
                fpath = uret_is_raporu(engine, vardiya_id)
                if fpath:
                    with open(fpath, "rb") as f:
                        st.download_button("⬇️ RAPORU İNDİR", f, 
                                          file_name=f"MAP_Vardiya_Raporu_{vardiya_id}.pdf", 
                                          mime="application/pdf")
    except ImportError:
        st.info("ℹ️ PDF modülü hazırlanıyor...")


# ─── Ana Fonksiyon ────────────────────────────────────────────────────────────
def render_map_module(engine=None):
    """MAP üretim takip modülünü render eder."""
    try:
        if not kullanici_yetkisi_var_mi("📦 MAP Üretim", "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz yok."); st.stop()

        if engine is None:
            engine = get_engine()

        _init_state()
        st.title("📦 MAP Makinası Üretim Takip")
        st.caption("Anlık çalışma/duruş, bobin ve fire kayıtları | EKL-URT-F-MAP-001")

        tab_vrd, tab_zaman, tab_bob, tab_fire, tab_rpr = st.tabs([
            "🟢 Vardiya", "🕹️ Kontrol Merkezi", "🎞️ Bobin", "🔥 Fire", "📊 Rapor"
        ])

        aktif = db.get_aktif_vardiya(engine)
        vardiya_id = int(aktif['id']) if aktif else st.session_state.get("map_aktif_vardiya_id")

        with tab_vrd:
            _tab_vardiya(engine)

        for tab, fn in [(tab_zaman, _tab_zaman), (tab_bob, _tab_bobin),
                        (tab_fire, _tab_fire), (tab_rpr, _tab_rapor)]:
            with tab:
                if not vardiya_id:
                    st.warning("⚠️ Önce Vardiya Tabından yeni bir vardiya başlatın.")
                else:
                    fn(engine, int(vardiya_id))
                    
    except Exception as e:
        st.error(f"🚨 **MODÜL HATASI:** {str(e)}")
        st.exception(e)
