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


def _render_live_timer(label, start_ts_str, end_ts_str=None, status="active"):
    """HTML/JS kullanarak sayfa yenilemeden sayan canlı sayaç.
    bitis_ts_str varsa sayaç o saniyede durur (Smart Timer).
    """
    bg_color = "#d4edda" if status == "active" else "#f8d7da"
    text_color = "#155724" if status == "active" else "#721c24"
    border_color = "#28a745" if status == "active" else "#dc3545"
    
    unique_id = f"timer_{int(time.time())}_{label.replace(' ','')}"
    
    # JavaScript logic for stopping
    stop_logic = ""
    if end_ts_str:
        stop_logic = f'const endTime = new Date("{end_ts_str.replace(" ", "T")}");'
    else:
        stop_logic = 'const endTime = null;'

    html_code = f"""
    <div style="background-color:{bg_color}; padding:15px; border-radius:12px; border:2px solid {border_color}; text-align:center; font-family:sans-serif; margin-bottom:5px;">
        <div style="font-size:12px; color:{text_color}; text-transform:uppercase; font-weight:bold; margin-bottom:2px;">{label}</div>
        <div id="{unique_id}" style="font-size:28px; font-weight:bold; color:{text_color};">00:00:00</div>
    </div>
    
    <script>
    (function() {{
        const startTime = new Date("{start_ts_str.replace(' ', 'T')}");
        {stop_logic}
        const timerElement = document.getElementById("{unique_id}");
        
        function update() {{
            const now = endTime ? endTime : new Date();
            const diff = Math.floor((now - startTime) / 1000);
            if (diff < 0) return;
            
            const h = Math.floor(diff / 3600);
            const m = Math.floor((diff % 3600) / 60);
            const s = diff % 60;
            
            timerElement.innerText = 
                h.toString().padStart(2, '0') + ":" + 
                m.toString().padStart(2, '0') + ":" + 
                s.toString().padStart(2, '0');
            
            if (endTime) return; // Eğer bitiş zamanı varsa döngüyü durdur
            setTimeout(update, 1000);
        }}
        update();
    }})();
    </script>
    """
    st.components.v1.html(html_code, height=95)


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
def _tab_vardiya(engine, aktif=None):
    # ─── 1. SEÇİLİ AKTİF VARDİYA BİLGİSİ ───
    if aktif:
        st.session_state.map_aktif_vardiya_id = int(aktif['id'])
        bas = aktif['baslangic_saati']
        st.success(f"✅ **{aktif['makina_no']}** | {aktif['vardiya_no']}. Vardiya | Başlangıç: **{bas}**")
        st.caption(f"👷 Operatör: **{aktif['operator_adi']}** | Şef: **{aktif['vardiya_sefi'] or '-'}**")
        
        notlar = st.text_area("📝 Vardiya Notu", value=aktif.get('notlar', '') or "", key=f"not_{aktif['id']}")
        
        st.divider()
        with st.popover(f"🔴 {aktif['makina_no']} VARDİYASINI KAPAT", use_container_width=True):
            st.warning(f"{aktif['makina_no']} vardiyasını kapatmak üzeresiniz. Emin misiniz?")
            uretim_final = st.number_input("Final Üretim Adedi", 0, 100000, value=int(aktif['gerceklesen_uretim']), key=f"final_{aktif['id']}")
            if st.button("EVET, KAPAT", use_container_width=True, type="primary", key=f"btn_kapat_{aktif['id']}"):
                db.kapat_vardiya(engine, int(aktif['id']), int(uretim_final))
                st.success(f"{aktif['makina_no']} kapatıldı!")
                time.sleep(1.0)
                st.rerun()

    # ─── 2. YENİ VARDİYA BAŞLATMA ───
    aktif_df = db.get_tum_aktif_vardiyalar(engine)
    aktif_names = aktif_df['makina_no'].tolist() if not aktif_df.empty else []
    bostaki = [m for m in MAP_MAKINA_LISTESI if m not in aktif_names]

    if bostaki:
        title = "➕ Yeni Makine (Vardiya) Başlat"
        
        # EĞER AKTİF VARDİYA YOKSA FORMU DOĞRUDAN GÖSTER (EXPANDERSIZ)
        if not aktif:
            st.subheader(title)
            st.info("📋 Boştaki makinelerden birini seçerek vardiyayı başlatın.")
            _render_yeni_vardiya_form(engine, bostaki)
        else:
            # AKTİF VARDİYA VARSA DİĞERLERİNİ EXPANDER İLE GÖSTER
            with st.expander(title, expanded=False):
                _render_yeni_vardiya_form(engine, bostaki)
    elif not aktif:
        st.warning("⚠️ Tüm makineler şu an aktif vardiyada.")

def _render_yeni_vardiya_form(engine, bostaki):
    # FORM ANAHTARI SABİT OLMALIDIR (time.time() kullanımı formu bozar)
    with st.form("yeni_vardiya_baslatma_formu"):
        c1, c2 = st.columns(2)
        makina = c1.selectbox("🏭 Makina Seçin", bostaki)
        vno = c2.selectbox("⏰ Vardiya No", [1, 2, 3])
        
        # OTO ATAMA: Sisteme giren kullanıcının adını otomatik getir ve kilitle (Hesap verebilirlik)
        aktif_kullanici = st.session_state.get('user', '')
        op = st.text_input("👷 Operatör Adı (Soyadı)", value=aktif_kullanici, disabled=True)
        sef = st.text_input("👔 Vardiya Şefi (boş bırakılabilir)")
        c3, c4, c5 = st.columns(3)
        bes = c3.number_input("Besleme Kişi", 0, 20, 4)
        kas = c4.number_input("Kasalama Kişi", 0, 20, 1)
        hiz = c5.number_input("🎯 Hedef Hız (pk/dk)", 0.1, 20.0, 4.2, step=0.1)
        if st.form_submit_button("🟢 MAKİNEYİ BAŞLAT", use_container_width=True, type="primary"):
            if not op.strip():
                st.error("Operatör adı zorunludur!")
            else:
                try:
                    vid = db.aç_vardiya(engine, makina, vno, op.strip(), sef.strip(),
                                        int(bes), int(kas), float(hiz))
                    db.insert_zaman_kaydi(engine, vid, "CALISIYOR")
                    st.session_state.map_aktif_vardiya_id = vid
                    st.session_state.map_selected_makina = makina # YENI: Baslatilan makineye gec
                    st.success(f"✅ {makina} Başlatıldı!")
                    time.sleep(0.5)
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))


# ─── Tab 2 — Kontrol Merkezi (ALL-IN-ONE) ───────────────────────────────────
def _tab_kontrol_merkezi(engine, vardiya_id):
    # Belirli bir vardiya ID'sine göre verileri çekelim (doğru yöntem)
    with engine.connect() as conn:
        aktif_df = db._read(conn, "SELECT * FROM map_vardiya WHERE id=:id", {"id": vardiya_id})
        aktif = aktif_df.iloc[0].to_dict() if not aktif_df.empty else None
    
    if not aktif:
        st.warning("🚨 Vardiya verisi bulunamadı."); return

    son = db.get_son_zaman_kaydi(engine, vardiya_id)
    durum = son['durum'] if son and aktif.get('durum') == 'ACIK' else "KAPALI"
    aktif_neden = (son.get('neden') or '') if son else ''

    # 1. MAKİNA DURUMU VE CANLI SAYAÇLAR (JS)
    c_status, c_timer1, c_timer2 = st.columns([2, 1, 1])
    
    with c_status:
        if durum == "CALISIYOR":
            label = "🟢 ÜRETİM DEVAM EDİYOR"
            st.markdown(f'<div style="background-color:#d4edda; padding:12px; border-radius:12px; border:2px solid #28a745; height:100px; display:flex; flex-direction:column; justify-content:center;">'
                        f'<h3 style="color:#155724; margin:0; font-size:20px;">{label}</h3>'
                        f'<p style="color:#155724; margin:0; font-size:14px;">Operatör: {aktif["operator_adi"]}</p></div>', unsafe_allow_html=True)
        elif durum == "DURUS":
            label = f"🔴 DURUŞ: {aktif_neden or 'Tanımlanmadı'}"
            st.markdown(f'<div style="background-color:#f8d7da; padding:12px; border-radius:12px; border:2px solid #dc3545; height:100px; display:flex; flex-direction:column; justify-content:center;">'
                        f'<h3 style="color:#721c24; margin:0; font-size:20px;">{label}</h3>'
                        f'<p style="color:#721c24; margin:0; font-size:14px;">Duruş Nedeni: {aktif_neden or "-"}</p></div>', unsafe_allow_html=True)
        else: # KAPALI
            label = "🏁 VARDIYA TAMAMLANDI"
            st.markdown(f'<div style="background-color:#e2e3e5; padding:12px; border-radius:12px; border:2px solid #6c757d; height:100px; display:flex; flex-direction:column; justify-content:center;">'
                        f'<h3 style="color:#383d41; margin:0; font-size:20px;">{label}</h3>'
                        f'<p style="color:#383d41; margin:0; font-size:14px;">Rapor Üretildi</p></div>', unsafe_allow_html=True)
    
    with c_timer1:
        # Mevcut durum süresi
        v_bitis = aktif.get('bitis_saati') # Eğer kapalıysa bitiş vardır
        end_ts = None
        if aktif.get('durum') == 'KAPALI':
            # Vardiya kapalıysa son kaydı bitirmiş olmalıyız
            end_ts = son['bitis_ts'] if son else None
            
        _render_live_timer("DURUM SÜRESİ", son['baslangic_ts'], end_ts_str=end_ts, status="active" if durum == "CALISIYOR" else "idle")

    with c_timer2:
        # Toplam Vardiya Süresi
        v_bas_ts = f"{aktif['tarih']} {aktif['baslangic_saati']}:00"
        v_end_ts = f"{aktif['tarih']} {aktif['bitis_saati']}:00" if aktif.get('durum') == 'KAPALI' else None
        _render_live_timer("TOPLAM VARDIYA", v_bas_ts, end_ts_str=v_end_ts, status="active")

    st.divider()

    # 2. ÜRETİM VE DURUŞ KONTROLLERİ (İKİ KOLON)
    col_l, col_r = st.columns([1, 1])

    with col_l:
        st.subheader("⚡ Duruş Yönetimi")
        if aktif.get('durum') == "ACIK":
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
        else:
            st.info("Vardiya kapalı. Duruş girişi yapılamaz.")

    with col_r:
        st.subheader("📦 Üretim & Kayıplar")
        # Canlı Üretim Girişi (KÜMÜLATİF)
        with st.expander("➕ Üretim Ekle", expanded=True):
            add_uretim = st.number_input("Eklenen Paket Adedi", 0, 10000, 100, step=10)
            if st.button("➕ ÜRETİMİ TOPLA VE KAYDET", use_container_width=True, type="primary"):
                db.update_kumulatif_uretim(engine, vardiya_id, add_uretim)
                st.toast(f"✅ {add_uretim} paket başarıyla eklendi!")
                time.sleep(0.5); st.rerun()
            st.caption(f"Güncel Toplam: **{aktif['gerceklesen_uretim']}** paket")

        st.write("")
        # Fire Girişi (One-Click / KÜMÜLATİF)
        with st.popover("🔥 Fire Ekle", use_container_width=True):
            f_mik = st.number_input("Eklenecek Fire Adedi", 1, 1000, 10)
            for i, tip in enumerate(MAP_FIRE_TIPLERI):
                if st.button(f"➕ {tip}", key=f"fire_in_{i}", use_container_width=True):
                    if _is_click_safe():
                        db.insert_fire(engine, vardiya_id, tip, int(f_mik))
                        st.toast(f"✅ {f_mik} adet {tip} eklendi!")
                        time.sleep(0.5); st.rerun()

        # Bobin Değişimi (ÜST/ALT KG)
        if st.button("🎞️ Bobin Değiştir", use_container_width=True):
            st.session_state.map_bobin_form = not st.session_state.map_bobin_form

        if st.session_state.map_bobin_form:
            with st.form("bobin_form_konsol"):
                lot = st.text_input("📦 LOT No")
                c_f1, c_f2 = st.columns(2)
                f_tip = c_f1.selectbox("🎞️ Film Tipi", ["Üst Film", "Alt Film"])
                c_b1, c_b2 = st.columns(2)
                bas_kg = c_b1.number_input("Yeni Bobin (KG)", 0.0, 100.0, 25.0)
                bit_kg = c_b2.number_input("Kalan Eskisi (KG)", 0.0, 100.0, 0.0)
                if st.form_submit_button("✅ BOBİNİ KAYDET"):
                    db.insert_bobin(engine, vardiya_id, lot, f_tip, bas_kg, bit_kg)
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

    # Hız farkı etiketi hazırlama
    hiz_fark = uretim.get('hiz_farki_pct', 0)
    emoji = "🔼" if hiz_fark > 0 else "🔽" if hiz_fark < 0 else "➖"
    hiz_fark_label = f"{emoji} {hiz_fark}%"

    # 1. KPI Kartları
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Üretim", f"{uretim['gerceklesen_uretim']} pk", f"Hedef: {uretim['teorik_uretim']}")
    c2.metric("OEE (Kul.)", f"%{ozet['kullanilabilirlik_pct']}")
    c3.metric("🔥 Fire", f"%{uretim['fire_pct']}", f"{uretim['fire_adet']} adet")
    c4.metric("🚀 Hız", f"{uretim['gercek_hiz']} pk/dk", f"{hiz_fark_label}")

    # 1.1 Toplam Süreler (Yeni Satır)
    st.write("---")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("⏱️ Toplam Vardiya", f"{ozet['toplam_vardiya_dk']} dk")
    s2.metric("🟢 Toplam Çalışma", f"{ozet['toplam_calisma_dk']} dk")
    s3.metric("🔴 Toplam Duruş", f"{ozet['toplam_durus_dk']} dk")
    s4.metric("☕ Mola", f"{ozet['mola_dk']} dk")

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
    
    # 3. KURUMSAL HTML/A4 RAPORU
    try:
        from .map_rapor_pdf import uret_is_raporu_html
        import json
        
        html_rapor = uret_is_raporu_html(engine, vardiya_id)
        if html_rapor:
            html_json = json.dumps(html_rapor)
            pdf_js = f"""
            <script>
            function printMapReport() {{
                var html = {html_json};
                var blob = new Blob([html], {{type: 'text/html;charset=utf-8'}});
                var url = URL.createObjectURL(blob);
                var win = window.open(url, '_blank');
                win.addEventListener('load', function() {{ setTimeout(function() {{ win.print(); }}, 600); }});
            }}
            </script>
            <button onclick="printMapReport()" style="width:100%; padding:15px 0; background:#8B0000; color:white; border:none; border-radius:10px; font-size:16px; font-weight:bold; cursor:pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
                🖨️ KURUMSAL RAPORU YAZDIR / PDF KAYDET
            </button>
            """
            st.components.v1.html(pdf_js, height=80)
        else:
            st.error("Rapor verileri hazırlanamadı.")
            
    except Exception as e:
        st.info(f"ℹ️ Rapor modülü hatası: {e}")


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

        # ─── ÇOKLU MAKİNE YÖNETİMİ (SIDEBAR) ───
        aktif_df = db.get_bugunku_vardiyalar(engine)
        aktif_sayisi = len(aktif_df)
        
        with st.sidebar:
            st.header("🏭 Makine Yönetimi")
            if aktif_sayisi > 0:
                # HIZLI GEÇİŞ BUTONLARI (Ana Alan İçin Hazırlık)
                options = []
                for _, row in aktif_df.iterrows():
                    prefix = "🟢" if row['durum'] == 'ACIK' else "🔴"
                    options.append(f"{prefix} {row['makina_no']} (V{row['vardiya_no']})")
                
                # Mevcut seçimi session_state üzerinden yönet
                if 'map_selected_makina_full' not in st.session_state or st.session_state.map_selected_makina_full not in options:
                    st.session_state.map_selected_makina_full = options[0]
                
                # Exception'ı önlemek için 'key' parametresi kullanmıyoruz, index ile state senkronu yapıyoruz.
                try:
                    current_idx = options.index(st.session_state.map_selected_makina_full)
                except ValueError:
                    current_idx = 0

                selected_label = st.selectbox(
                    "📱 Yönetilen Makina (Bugün)", 
                    options=options,
                    index=current_idx
                )
                
                if selected_label != st.session_state.map_selected_makina_full:
                    st.session_state.map_selected_makina_full = selected_label
                    st.rerun()

                # Seçilen label'dan gerçek makine adını ve durumunu ayıkla
                # Format: "🟢 MAP-01 (V1)"
                selected_makina_raw = selected_label[2:].split(" (")[0]
                selected_vno = int(selected_label.split("(V")[1].replace(")", ""))
                
                # SADECE SEÇİLEN MAKİNEYE VE VARDİYAYA AİT KAYDI BUL
                secili_df = aktif_df[(aktif_df['makina_no'] == selected_makina_raw) & (aktif_df['vardiya_no'] == selected_vno)]
                if not secili_df.empty:
                    aktif = secili_df.iloc[0].to_dict()
                    vardiya_id = int(aktif['id'])
                else:
                    # Fallback (Görsel bug olursa veya makine deaktif edildiyse)
                    aktif = aktif_df.iloc[0].to_dict()
                    vardiya_id = int(aktif['id'])
                if aktif_sayisi > 1:
                    st.divider()
                    st.subheader("Diğer Aktif Makineler")
                    for _, row in aktif_df.iterrows():
                        if row['makina_no'] != selected_makina:
                            st.success(f"🟢 {row['makina_no']} (ID: {row['id']})")
            else:
                st.info("Şu an aktif vardiya yok.")
                aktif = None
                vardiya_id = None

        # Eğer aktif vardiya yoksa son kapatılana bak (opsiyonel)
        if not aktif:
            son_kapatilan = db.get_son_kapatilan_vardiya(engine)
            if son_kapatilan:
                vardiya_id = int(son_kapatilan['id'])
                st.info(f"ℹ️ Şu an aktif bir vardiya yok. **Son Kapatılan Vardiya (ID: {vardiya_id})** verileri gösteriliyor.")
            else:
                vardiya_id = st.session_state.get("map_aktif_vardiya_id")

        if vardiya_id:
            st.session_state.map_aktif_vardiya_id = vardiya_id

        # ─── HIZLI MAKİNE GEÇİŞ HUB (Üst Menü) ───
        if aktif_sayisi > 1:
            st.write("### 🕹️ Hızlı Makine Geçişi")
            m_cols = st.columns(min(aktif_sayisi, 4))
            for i, (_, row) in enumerate(aktif_df.iterrows()):
                m_no = row['makina_no']
                is_active = (m_no == st.session_state.map_selected_makina)
                btn_type = "primary" if is_active else "secondary"
                icon = "✅" if is_active else "⚪"
                if m_cols[i % 4].button(f"{icon} {m_no}", key=f"btn_switch_{m_no}", type=btn_type, use_container_width=True):
                    st.session_state.map_selected_makina = m_no
                    st.rerun()
            st.write("---")

        tab_vrd, tab_ctrl, tab_rpr = st.tabs([
            "🟢 Vardiya", "🕹️ Kontrol Merkezi", "📊 Rapor"
        ])

        with tab_vrd:
            _tab_vardiya(engine, aktif)

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
