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
    "ARIZA / BAKIM", "SETUP / AYAR", "ÜRETİM BEKLEME",
    "TEMİZLİK / SANİTASYON", "DİĞER",
]
MAP_FIRE_TIPLERI = [
    "Bobin Başı Fire", "Bobin Sonu Fire", "Film Değişimi Fire",
    "Sızdırmazlık / Kaçak", "Yırtık / Delik Film", "Gaz Hatası",
    "Besleme Hatası", "Operatör Hatası", "Diğer",
]
_TZ = pytz.timezone("Europe/Istanbul")


# ─── UI Helpers (Mobile & Live) ────────────────────────────────────────────────
def _inject_custom_css():
    """Mobil uyumlu ve profesyonel görünüm için CSS."""
    st.markdown("""
        <style>
        /* Büyük Butonlar (Mobil için) */
        .stButton > button {
            height: 75px !important;
            font-size: 18px !important;
            font-weight: bold !important;
            border-radius: 15px !important;
            margin-bottom: 12px !important;
            transition: all 0.3s ease;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .stButton > button:active {
            transform: scale(0.95);
            box-shadow: 0 2px 3px rgba(0,0,0,0.2);
        }
        /* Dashboard Kartları */
        [data-testid="stMetricValue"] {
            font-size: 28px !important;
        }
        /* Sekme Fontları */
        .stTabs [data-baseweb="tab"] {
            font-size: 18px !important;
            padding: 10px 20px !important;
        }
        /* Mobil Genişlik */
        @media (max-width: 640px) {
            .stButton > button {
                height: 65px !important;
                font-size: 16px !important;
            }
        }
        </style>
    """, unsafe_allow_html=True)


def _render_live_timer(label, start_ts_str, status="active"):
    """HTML/JS kullanarak sayfa yenilemeden sayan canlı sayaç."""
    # start_ts_str format: "YYYY-MM-DD HH:MM:SS"
    bg_color = "#d4edda" if status == "active" else "#f8d7da"
    text_color = "#155724" if status == "active" else "#721c24"
    border_color = "#28a745" if status == "active" else "#dc3545"
    
    unique_id = f"timer_{int(time.time())}"
    
    html_code = f"""
    <div style="background-color:{bg_color}; padding:15px; border-radius:12px; border:2px solid {border_color}; text-align:center; font-family:sans-serif;">
        <div style="font-size:14px; color:{text_color}; text-transform:uppercase; font-weight:bold; margin-bottom:5px;">{label}</div>
        <div id="{unique_id}" style="font-size:32px; font-weight:bold; color:{text_color};">00:00:00</div>
    </div>
    
    <script>
    (function() {{
        const startTime = new Date("{start_ts_str.replace(' ', 'T')}");
        const timerElement = document.getElementById("{unique_id}");
        
        function update() {{
            const now = new Date();
            const diff = Math.floor((now - startTime) / 1000);
            if (diff < 0) return;
            
            const h = Math.floor(diff / 3600);
            const m = Math.floor((diff % 3600) / 60);
            const s = diff % 60;
            
            timerElement.innerText = 
                h.toString().padStart(2, '0') + ":" + 
                m.toString().padStart(2, '0') + ":" + 
                s.toString().padStart(2, '0');
        }}
        
        setInterval(update, 1000);
        update();
    }})();
    </script>
    """
    st.components.v1.html(html_code, height=100)


# ─── Session State Bootstrap ──────────────────────────────────────────────────
def _init_state():
    defaults = {
        "map_aktif_vardiya_id": None,
        "map_son_tık_ts": 0,
        "map_bobin_form": False,
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
        st.caption(f"👷 Operatör: **{aktif['operator_adi']}** | Şef: **{aktif['vardiya_sefi'] or '-'}**")
        
        # Vardiya Notları bu tabda kalabilir
        notlar = st.text_area("📝 Vardiya Notu", value=aktif.get('notlar', '') or "")
        if st.button("💾 Notu Güncelle"):
            # Not güncelleme logic'i db katmanında yokmuş, geçici olarak insert_fire gibi bir yapı gerekebilir 
            # veya kapat_vardiya'yı notlar için genişletebiliriz. Şimdilik sadece gösteriyoruz.
            pass

        st.divider()
        # 13. Adam: Yanlışlıkla vardiya kapatma koruması
        with st.popover("🔴 VARDİYAYI KAPAT (Günü Bitir)", use_container_width=True):
            st.warning("Vardiyayı kapatmak istediğinize emin misiniz? Bu işlem geri alınamaz.")
            uretim_final = st.number_input("Final Üretim Adedi (Toplam)", 0, 100000, value=int(aktif['gerceklesen_uretim']))
            if st.button("EVET, VARDİYAYI KAPAT", use_container_width=True, type="primary"):
                db.kapat_vardiya(engine, int(aktif['id']), int(uretim_final))
                st.session_state.map_aktif_vardiya_id = None
                st.success("Vardiya başarıyla kapatıldı!")
                time.sleep(0.5)
                st.rerun()


# ─── Tab 2 — Kontrol Merkezi (ALL-IN-ONE) ───────────────────────────────────
def _tab_kontrol_merkezi(engine, vardiya_id):
    aktif = db.get_aktif_vardiya(engine) # Güncel veri için tekrar çek
    if not aktif: return

    son = db.get_son_zaman_kaydi(engine, vardiya_id)
    durum = son['durum'] if son else "CALISIYOR"
    aktif_neden = son.get('neden', '') if son else ''

    # 1. MAKİNA DURUMU VE CANLI SAYAÇLAR (JS)
    c_status, c_timer1, c_timer2 = st.columns([2, 1, 1])
    
    with c_status:
        if durum == "CALISIYOR":
            label = "🟢 ÜRETİM DEVAM EDİYOR"
            st.markdown(f'<div style="background-color:#d4edda; padding:12px; border-radius:12px; border:2px solid #28a745; height:100px; display:flex; flex-direction:column; justify-content:center;">'
                        f'<h3 style="color:#155724; margin:0; font-size:20px;">{label}</h3>'
                        f'<p style="color:#155724; margin:0; font-size:14px;">Operatör: {aktif["operator_adi"]}</p></div>', unsafe_allow_html=True)
        else:
            label = f"🔴 DURUŞ: {aktif_neden}"
            st.markdown(f'<div style="background-color:#f8d7da; padding:12px; border-radius:12px; border:2px solid #dc3545; height:100px; display:flex; flex-direction:column; justify-content:center;">'
                        f'<h3 style="color:#721c24; margin:0; font-size:20px;">{label}</h3>'
                        f'<p style="color:#721c24; margin:0; font-size:14px;">Duruş Nedeni: {aktif_neden}</p></div>', unsafe_allow_html=True)
    
    with c_timer1:
        # Mevcut durum süresi (CALISIYOR veya DURUS başladığından beri)
        _render_live_timer("DURUM SÜRESİ", son['baslangic_ts'], status="active" if durum == "CALISIYOR" else "idle")

    with c_timer2:
        # Toplam Vardiya Süresi (Vardiya başladığından beri)
        # aktif['baslangic_saati'] 'HH:MM' formatında, tarih ise 'YYYY-MM-DD'
        v_bas_ts = f"{aktif['tarih']} {aktif['baslangic_saati']}:00"
        _render_live_timer("TOPLAM VARDIYA", v_bas_ts, status="active")

    st.divider()

    # 2. ÜRETİM VE DURUŞ KONTROLLERİ (İKİ KOLON)
    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.subheader("⚡ Duruş Yönetimi")
        if durum == "CALISIYOR":
            for i, ned in enumerate(MAP_DURUS_NEDENLERI):
                if st.button(f"🔻 {ned}", key=f"durus_{i}", use_container_width=True):
                    if _is_click_safe():
                        db.insert_zaman_kaydi(engine, vardiya_id, "DURUS", neden=ned)
                        st.rerun()
        else:
            if st.button("🟢 İŞE BAŞLA", use_container_width=True, type="primary", key="btn_ise_basla"):
                if _is_click_safe():
                    db.insert_zaman_kaydi(engine, vardiya_id, "CALISIYOR")
                    st.rerun()

    with col_r:
        st.subheader("📦 Üretim & Kayıplar")
        # Canlı Üretim Girişi
        yeni_uretim = st.number_input("Toplam Üretilen Paket", 0, 100000, value=int(aktif['gerceklesen_uretim']), step=10)
        if yeni_uretim != int(aktif['gerceklesen_uretim']):
            if st.button("💾 Üretimi Guncelle", use_container_width=True):
                # map_db'de bağımsız bir update_uretim fonksiyonu yok, ama kapat_vardiya mantığıyla benzer bir update işimizi görür.
                # Şema güncellenirken eklenen gerceklesen_uretim'i burada update edebiliriz.
                with engine.begin() as conn:
                    conn.execute(db.text("UPDATE map_vardiya SET gerceklesen_uretim=:u WHERE id=:id"), 
                                 {"u": int(yeni_uretim), "id": vardiya_id})
                st.success("Üretim güncellendi!"); time.sleep(0.5); st.rerun()

        st.write("")
        # Fire Girişi (One-Click)
        with st.popover("🔥 Fire Kaydet", use_container_width=True):
            f_mik = st.number_input("Fire Adedi", 1, 1000, 1)
            for i, tip in enumerate(MAP_FIRE_TIPLERI):
                if st.button(tip, key=f"fire_in_{i}", use_container_width=True):
                    if _is_click_safe():
                        db.insert_fire(engine, vardiya_id, tip, int(f_mik))
                        st.success(f"{f_mik} adet {tip} kaydedildi!")
                        time.sleep(0.5); st.rerun()

        # Bobin Değişimi
        if st.button("🎞️ Bobin Değiştir", use_container_width=True):
            st.session_state.map_bobin_form = not st.session_state.map_bobin_form

        if st.session_state.map_bobin_form:
            with st.form("bobin_form_konsol"):
                lot = st.text_input("📦 LOT No")
                c_b1, c_b2 = st.columns(2)
                bit_m = c_b1.number_input("Kalan (eski m)", 0.0, 1000.0, 0.0)
                bas_m = c_b2.number_input("Yeni (m)", 0.0, 1000.0, 300.0)
                if st.form_submit_button("✅ BOBİNİ KAYDET"):
                    db.insert_bobin(engine, vardiya_id, lot, bit_m, "", bas_m)
                    st.session_state.map_bobin_form = False
                    st.success("Bobin kaydedildi!"); time.sleep(0.5); st.rerun()

    st.divider()

    # 3. KAYIT GEÇMİŞİ (EXPANDER)
    with st.expander("🕒 Zaman Çizelgesi ve Geçmiş"):
        df_z = db.get_zaman_cizelgesi(engine, vardiya_id)
        if not df_z.empty:
            st.dataframe(df_z, use_container_width=True, hide_index=True)
            if st.button("🗑️ Son Zaman Kaydını Sil"):
                db.sil_son_zaman_kaydi(engine, vardiya_id); st.rerun()
        
        st.write("**🎞️ Son Bobinler**")
        df_b = db.get_bobinler(engine, vardiya_id)
        if not df_b.empty:
            st.dataframe(df_b[['sira_no', 'degisim_ts', 'bobin_lot', 'kullanilan_m']], use_container_width=True)

        st.write("**🔥 Son Fireler**")
        df_f = db.get_fire_kayitlari(engine, vardiya_id)
        if not df_f.empty:
            st.dataframe(df_f[['fire_tipi', 'miktar_adet', 'olusturma_ts']], use_container_width=True)


# ─── Tab 3 — Rapor (LIVE DASHBOARD) ───────────────────────────────────────────
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

    # 2. Grafikler
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
    
    # 3. PDF RAPORU
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
                else:
                    st.error("PDF üretilemedi.")
    except Exception as e:
        st.info(f"ℹ️ PDF modülü hatası: {e}")


# ─── Ana Fonksiyon ────────────────────────────────────────────────────────────
def render_map_module(engine=None):
    """MAP üretim takip modülünü render eder."""
    try:
        if not kullanici_yetkisi_var_mi("📦 MAP Üretim", "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz yok."); st.stop()

        if engine is None:
            engine = get_engine()

        _init_state()
        _inject_custom_css()  # Mobil CSS enjeksiyonu
        st.title("📦 MAP Makinası Üretim Takip")
        st.caption("EKLERİSTAN QMS — Verimlilik Odaklı Operatör Paneli")

        tab_vrd, tab_ctrl, tab_rpr = st.tabs([
            "🟢 Vardiya", "🕹️ Kontrol Merkezi", "📊 Rapor"
        ])

        aktif = db.get_aktif_vardiya(engine)
        vardiya_id = int(aktif['id']) if aktif else st.session_state.get("map_aktif_vardiya_id")

        with tab_vrd:
            _tab_vardiya(engine)

        with tab_ctrl:
            if not vardiya_id:
                st.warning("⚠️ Önce Vardiya Tabından yeni bir vardiya başlatın.")
            else:
                _tab_kontrol_merkezi(engine, int(vardiya_id))

        with tab_rpr:
            if not vardiya_id:
                st.warning("⚠️ Analiz için aktif bir vardiya olmalıdır.")
            else:
                _tab_rapor(engine, int(vardiya_id))
                    
    except Exception as e:
        st.error(f"🚨 **MODÜL HATASI:** {str(e)}")
        st.exception(e)
