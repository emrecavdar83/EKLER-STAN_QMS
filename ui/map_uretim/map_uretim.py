import streamlit as st
import pandas as pd
from datetime import datetime
import pytz, time

from database.connection import get_engine
from . import map_db as db
from . import map_hesap as hesap
from logic.auth_logic import kullanici_yetkisi_var_mi, audit_log_kaydet

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

def get_istanbul_time():
    """Anayasa v3.1: Standart İstanbul zamanını döndürür."""
    now = datetime.now(_TZ) if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()
    return now.replace(microsecond=0)


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
    """13. Adam: Arka arkaya hızlı tıklama koruması (0.4 sn)."""
    now = time.time()
    if now - st.session_state.map_son_tık_ts < 0.4:
        return False
    st.session_state.map_son_tık_ts = now
    return True


# ─── Tab 1 — Vardiya ──────────────────────────────────────────────────────────
def _tab_vardiya(engine, aktif=None, df_aktif_vardiyalar=None):
    # v4.0.5: Önemli - Seçili makine ismini session_state'ten güvenli bir şekilde al
    secili_label = st.session_state.get('map_selected_makina_full', '⚪ MAP-01 (V1)')
    secili_makina_raw = secili_label[2:].split(" (")[0]

    # v4.0.5: Önbelleksiz (Live Check) Kontrolü - UI senkronizasyonu için kritik denetim
    aktif_item = db.get_aktif_vardiya_live(engine, secili_makina_raw)
    
    if not aktif_item:
        _render_yeni_vardiya_form(engine, [secili_makina_raw], varsayilan_makina=secili_makina_raw)
    else:
        # Vardiya Aktif Görünümü (Listeden değil, doğrudan canlı kayıttan al)
        aktif = aktif_item
        vardiya_id = int(aktif['id'])
        st.session_state.map_aktif_vardiya_id = int(aktif['id']) if pd.notnull(aktif['id']) else 0
        bas = aktif['baslangic_saati']
        tarih = aktif['tarih']
        durum = aktif.get('durum', 'ACIK')
        
        if durum == 'ACIK':
            st.success(f"🟢 **{aktif['makina_no']}** | {aktif['vardiya_no']}. Vardiya | Başlangıç: **{tarih} {bas}**")
            st.caption(f"👷 Operatör: **{aktif['operator_adi']}** | Şef: **{aktif['vardiya_sefi'] or '-'}**")
            notlar = st.text_area("📝 Vardiya Notu", value=aktif.get('notlar', '') or "", key=f"not_{aktif['id']}")
            
            st.divider()
            with st.popover(f"🔴 {aktif['makina_no']} VARDİYASINI KAPAT", use_container_width=True):
                st.warning(f"{aktif['makina_no']} vardiyasını kapatmak üzeresiniz. Emin misiniz?")
                uretim_final = st.number_input("Final Üretim Adedi", 0, 100000, value=int(aktif['gerceklesen_uretim']) if pd.notnull(aktif['gerceklesen_uretim']) else 0, key=f"final_{aktif['id']}")
                if st.button("EVET, KAPAT", use_container_width=True, type="primary", key=f"btn_kapat_{aktif['id']}"):
                    kapatan_id = st.session_state.get('user_id', 0)
                    db.kapat_vardiya(engine, int(aktif['id']), int(uretim_final), int(kapatan_id))
                    # ÖNEMLİ: Kapatma sonrası state temizliği (Saçma görünümü engeller)
                    st.session_state.map_aktif_vardiya_id = None
                    if 'map_selected_makina_full' in st.session_state:
                         # Seçili makine ismini "🔴" (Kapalı) olarak güncelle ki sidebar doğru seçsin
                         st.session_state.map_selected_makina_full = str(st.session_state.map_selected_makina_full).replace("🟢", "🔴")
                    
                    st.success(f"{aktif['makina_no']} kapatıldı!")
                    st.rerun()
        else:
            # KAPALI VARDİYA: Minimal Gösterim (Sadece durum özeti)
            st.info(f"🏁 **{aktif['makina_no']} (KAPALI)** | {aktif['vardiya_no']}. Vardiya | Başlangıç: **{tarih} {bas}**")
            # Detaylar gizlendi (Anayasa Dinamiklik İlkesi)

    # ─── 2. YENİ VARDİYA BAŞLATMA ───
    acik_df = df_aktif_vardiyalar if df_aktif_vardiyalar is not None else db.get_tum_aktif_vardiyalar(engine)
    # Kritik: İsimleri temizle ve tekilleştir (Duble makine hatasını önle)
    acik_isimler = list(set([str(n).strip().upper() for n in acik_df['makina_no'].tolist()])) if not acik_df.empty else []
    bostaki = [m for m in MAP_MAKINA_LISTESI if m.strip().upper() not in acik_isimler]

    if bostaki:
        # Eğer yanda seçili olan makina zaten 'bostaki' ise, formu otomatik aç ve yukarıdaki 'Kapalı' barını gizle
        secili_makina = str(aktif['makina_no']).strip() if aktif else None
        makina_bos_mu = secili_makina in bostaki if secili_makina else False
        
        # Eğer makina boşsa, yukarıdaki 'Vardiya Tamamlanmıştır' bilgisini tekrar göstermeye gerek yok (Anayasa Dinamiklik)
        if makina_bos_mu and aktif and aktif.get('durum') == 'KAPALI':
            st.empty() # Placeholder for UI cleanup
        
        title = "➕ Yeni Makine (Vardiya) Başlat"
        with st.expander(title, expanded=makina_bos_mu or not aktif):
            _render_yeni_vardiya_form(engine, bostaki, varsayilan_makina=secili_makina if makina_bos_mu else bostaki[0])
    elif not aktif:
        st.warning("⚠️ Tüm makineler şu an aktif vardiyada.")

def _render_yeni_vardiya_form(engine, bostaki, varsayilan_makina=None):
    # FORM ANAHTARI SABİT OLMALIDIR (time.time() kullanımı formu bozar)
    with st.form("yeni_vardiya_baslatma_formu"):
        c1, c2 = st.columns(2)
        idx = 0
        if varsayilan_makina in bostaki:
            idx = bostaki.index(varsayilan_makina)
        makina = c1.selectbox("🏭 Makina Seçin", bostaki, index=idx)
        vno = c2.selectbox("⏰ Vardiya No", [1, 2, 3])
        
        # OTO ATAMA: Sisteme giren kullanıcının adını otomatik getir ve kilitle (Hesap verebilirlik)
        aktif_kullanici_full = st.session_state.get('user_fullname', st.session_state.get('user', ''))
        op = st.text_input("👷 Operatör Adı (Soyadı)", value=aktif_kullanici_full, disabled=True)
        sef = st.text_input("👔 Vardiya Şefi (boş bırakılabilir)")
        c3, c4, c5 = st.columns(3)
        bes = c3.number_input("Besleme Kişi", 0, 20, 4)
        kas = c4.number_input("Kasalama Kişi", 0, 20, 1)
        hiz = c5.number_input("🎯 Hedef Hız (pk/dk)", 0.1, 20.0, 4.2, step=0.1)
        if st.form_submit_button("🟢 MAKİNEYİ BAŞLAT", use_container_width=True, type="primary"):
            if not op.strip():
                st.error("Operatör adı zorunludur!")
            else:
                with st.spinner("Makine sistemleri başlatılıyor..."):
                    try:
                        acan_id = st.session_state.get('user_id', 0)
                        vid = db.aç_vardiya(engine, makina, vno, op.strip(), int(acan_id), sef.strip(),
                                            int(bes), int(kas), float(hiz))
                        # İlk zaman kaydını aç (CALISIYOR)
                        db.insert_zaman_kaydi(engine, vid, "CALISIYOR")
                        
                        # v4.0.3: Önemli - Rerun öncesi state güncellenmeli (EKL-MAP-FIX-007)
                        prefix = "🟢"
                        st.session_state.map_aktif_vardiya_id = vid
                        st.session_state.map_selected_makina_full = f"{prefix} {makina} (V{vno})"
                        
                        st.success(f"✅ {makina} Başlatıldı! Kontrol merkezine yönlendiriliyorsunuz...")
                        time.sleep(1.2)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Başlatma Hatası: {str(e)}")


# ─── Tab 2 — Kontrol Merkezi (ALL-IN-ONE) ───────────────────────────────────
def _tab_kontrol_merkezi(engine, vardiya_id, df_vardiya=None, df_zaman=None, df_fire=None, df_bobin=None):
    # Belirli bir vardiya ID'sine göre verileri çekelim (doğru yöntem)
    if df_vardiya is None:
        with engine.connect() as conn:
            df_vardiya = db._read(conn, "SELECT * FROM map_vardiya WHERE id=:id", {"id": vardiya_id})
    
    aktif = df_vardiya.iloc[0].to_dict() if not df_vardiya.empty else None
    
    if not aktif:
        st.warning("🚨 Vardiya verisi bulunamadı."); return

    if df_zaman is None or df_zaman.empty:
        son = db.get_son_zaman_kaydi(engine, vardiya_id)
    else:
        son = df_zaman.sort_values('id', ascending=False).iloc[0].to_dict() if not df_zaman.empty else None
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
        
        # Güvenlik: son['baslangic_ts'] None gelirse sayacı gösterme (Saçma Görünüm Fix)
        if son and son.get('baslangic_ts'):
            _render_live_timer("Durum Süresi", son['baslangic_ts'], end_ts_str=end_ts, status="active" if durum == "CALISIYOR" else "idle")
        else:
            st.warning("⏱️ Zaman kaydı başlatılamadı.")

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
                st.rerun()
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
                        st.rerun()

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
                    st.toast("✅ Bobin kaydedildi!")
                    st.rerun()

    st.divider()
    
    # 🛠️ ADMIN DÜZELTME PANELI (Anayasa Madde 5 & 10)
    user_rol = st.session_state.get('user_rol', 'Personel')
    if user_rol == 'ADMIN':
        with st.expander("🛠️ Admin Net Toplam Düzeltme"):
            st.warning("Bu alan sadece hatalı toplamları doğrudan düzeltmek içindir. Mevcut toplamı ezer.")
            current_total = int(aktif['gerceklesen_uretim']) if pd.notnull(aktif['gerceklesen_uretim']) else 0
            c_adj1, c_adj2 = st.columns([1, 2])
            new_total = c_adj1.number_input("Yeni Net Toplam Miktar", 0, 100000, current_total, step=1, key="new_total_val")
            adj_reason = c_adj2.text_input("Düzeltme Nedeni (Zorunlu)", key="adj_reason_net")
            
            if st.button("⚠️ NET TOPLAMI GÜNCELLE VE KAYDET", use_container_width=True, type="primary"):
                if new_total == current_total:
                    st.error("Yeni toplam mevcut toplamla aynıdır.")
                elif not adj_reason.strip():
                    st.error("Düzeltme nedeni girmek zorunludur.")
                elif _is_click_safe():
                    # 1. DB Güncelleme (set_net_uretim)
                    db.set_net_uretim(engine, vardiya_id, new_total)
                    # 2. Audit Log (Anayasa Madde 6)
                    audit_log_kaydet("MAP_URETIM_DUZELTME_NET", f"Vardiya ID: {vardiya_id}, Eski: {current_total}, Yeni: {new_total}, Neden: {adj_reason}")
                    st.success(f"✅ Üretim net toplamı {new_total} adet olarak güncellendi.")
                    time.sleep(1)
                    st.rerun()

    st.divider()

    # 3. KAYIT GEÇMİŞİ (EXPANDER)
    with st.expander("🕒 Zaman Çizelgesi ve Geçmiş"):
        df_z = df_zaman if df_zaman is not None else db.get_zaman_cizelgesi(engine, vardiya_id)
        if not df_z.empty:
            st.dataframe(df_z, use_container_width=True, hide_index=True)
            if st.button("🗑️ Son Zaman Kaydını Sil"):
                db.sil_son_zaman_kaydi(engine, vardiya_id); st.rerun()
        
        st.write("**🎞️ Son Bobinler**")
        df_b = df_bobin if df_bobin is not None else db.get_bobinler(engine, vardiya_id)
        if not df_b.empty:
            st.dataframe(df_b[['sira_no', 'degisim_ts', 'bobin_lot', 'kullanilan_m']], use_container_width=True)

        st.write("**🔥 Son Fireler**")
        df_f = df_fire if df_fire is not None else db.get_fire_kayitlari(engine, vardiya_id)
        if not df_f.empty:
            st.dataframe(df_f[['fire_tipi', 'miktar_adet', 'olusturma_ts']], use_container_width=True)


# ─── Tab 3 — Rapor (LIVE DASHBOARD) ───────────────────────────────────────────
def _tab_rapor(engine, vardiya_id, df_vardiya=None, df_zaman=None, df_fire=None):
    st.subheader("📊 Canlı Vardiya Dashboard")
    ozet = hesap.hesapla_sure_ozeti(engine, vardiya_id, df_zaman=df_zaman, df_vardiya=df_vardiya)
    uretim = hesap.hesapla_uretim(engine, vardiya_id, df_vardiya=df_vardiya, df_fire=df_fire, sure_ozeti=ozet)
    
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
        # v4.0.2: df_zaman paslanarak mükerrer DB sorgusu önlendi
        durus_df = pd.DataFrame(hesap.hesapla_durus_ozeti(engine, vardiya_id, df_zaman=df_zaman))
        if not durus_df.empty:
            st.bar_chart(durus_df.set_index('neden')['toplam_dk'])
        else:
            st.info("Henüz duruş kaydı yok.")

    with col_right:
        st.write("**🔥 Fire Tipleri (adet)**")
        # v4.0.2: df_fire paslanarak mükerrer DB sorgusu önlendi
        fire_df = pd.DataFrame(hesap.hesapla_fire_ozeti(engine, vardiya_id, df_fire=df_fire))
        if not fire_df.empty:
            st.bar_chart(fire_df.set_index('fire_tipi')['miktar'])
        else:
            st.info("Henüz fire kaydı yok.")

    st.divider()
    
    # 3. KURUMSAL HTML/A4 RAPORU (Lazy Loading - Sadece Butona Basıldığında)
    try:
        from .map_rapor_pdf import uret_is_raporu_html
        import json
        
        # v4.0.2: Ağır rapor üretimini buton arkasına aldık (10sn+ tasarruf)
        if st.button("📄 KURUMSAL RAPOR ÖNİZLEMESİ OLUŞTUR", use_container_width=True):
            html_rapor = uret_is_raporu_html(engine, vardiya_id, df_zaman=df_zaman, df_fire=df_fire)
            if html_rapor:
                html_json = json.dumps(html_rapor)
                pdf_js = f"""
                <script>
                function printMapReport() {{
                    var html = {html_json};
                    var blob = new Blob([html], {{type: 'text/html;charset=utf-8'}});
                    var url = URL.createObjectURL(blob);
                    var win = window.open(url, '_blank');
                    win.document.title = "MAP MAKİNASI ÜRETİM İŞ RAPORU"; 
                    win.addEventListener('load', function() {{ setTimeout(function() {{ win.print(); }}, 800); }});
                }}
                printMapReport(); // Butona basıldığında otomatik tetikle
                </script>
                <div style="text-align:center; padding:10px; background:#f8f9fa; border:1px solid #ddd; border-radius:10px;">
                    <p>✅ Rapor başarıyla hazırlandı. Tarayıcınızın "Yazdır" penceresi açılmamışsa aşağıdaki butona tıklayın.</p>
                    <button onclick="printMapReport()" style="width:100%; padding:15px 0; background:#8B0000; color:white; border:none; border-radius:10px; font-size:16px; font-weight:bold; cursor:pointer;">
                        🖨️ RAPORU TEKRAR YAZDIR / PDF KAYDET
                    </button>
                </div>
                """
                st.components.v1.html(pdf_js, height=180)
            else:
                st.error("Rapor verileri hazırlanamadı.")
            
    except Exception as e:
        st.info(f"ℹ️ Rapor modülü hatası: {e}")


# ─── Ana Fonksiyon ────────────────────────────────────────────────────────────
def render_map_module(engine=None):
    """MAP üretim takip modülünü render eder. (v4.0.2 stabilized)"""
    try:
        # 1. YETKİ VE TEMEL BİLEŞENLER
        if not kullanici_yetkisi_var_mi("📦 MAP Üretim", "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz yok."); st.stop()

        if engine is None: engine = get_engine()
        _init_state(); _inject_custom_css()
        
        # 2. VERİ ÇEKME (TOP-LEVEL & CACHED) - v4.0.2: Tüm çekimler en başa alındı
        all_active_df = db.get_tum_aktif_vardiyalar(engine)
        bugun_df = db.get_bugunku_vardiyalar(engine)
        
        st.title("📦 MAP Makinası Üretim Takip")
        st.caption("EKLERİSTAN QMS — Verimlilik Odaklı Operatör Paneli")

        # 3. MAKİNE SEÇİM MANTIĞI (SIDEBAR)
        with st.sidebar:
            st.header("🏭 Makine Yönetimi")
            mode = st.radio("Seçim Modu", ["Bugün", "Arşiv (Geçmiş)"], horizontal=True)
            aktif, vardiya_id = None, None
            aktif_sayisi = 0

            if mode == "Bugün":
                aktif_df = pd.concat([all_active_df, bugun_df]).drop_duplicates('id')
                if not aktif_df.empty:
                    aktif_df = aktif_df.sort_values('id', ascending=False).drop_duplicates('makina_no').sort_values('makina_no')
                    aktif_sayisi = len(aktif_df)
                    options = []
                    acik_index = 0
                    for i, (_, row) in enumerate(aktif_df.iterrows()):
                        prefix = "🟢" if row['durum'] == 'ACIK' else "🔴"
                        label = f"{prefix} {row['makina_no']} (V{row['vardiya_no']})"
                        options.append(label)
                        if row['durum'] == 'ACIK' and acik_index == 0: acik_index = i
                    
                    # v4.0.5: Akıllı Eşleşme - Eğer seçili etiket listede yoksa (Örn: Beyaz->Yeşil geçişi), 
                    # listedeki aynı makine isimli olanı bul ve seçimi ona kaydır.
                    if 'map_selected_makina_full' not in st.session_state or st.session_state.map_selected_makina_full not in options:
                        current_raw = st.session_state.get('map_selected_makina_full', '')[2:].split(" (")[0]
                        found = False
                        if current_raw:
                            for i, opt in enumerate(options):
                                if current_raw in opt:
                                    st.session_state.map_selected_makina_full = opt
                                    found = True; break
                        if not found:
                            st.session_state.map_selected_makina_full = options[acik_index]
                    
                    current_idx = options.index(st.session_state.map_selected_makina_full)
                    selected_label = st.selectbox("📱 Yönetilen Makina (Bugün)", options=options, index=current_idx)
                    
                    if selected_label != st.session_state.get('map_selected_makina_full'):
                        st.session_state.map_selected_makina_full = selected_label
                        st.rerun()

                    selected_makina_raw = selected_label[2:].split(" (")[0]
                    selected_vno = int(selected_label.split("(V")[1].replace(")", ""))
                    secili_df = aktif_df[(aktif_df['makina_no'] == selected_makina_raw) & (aktif_df['vardiya_no'] == selected_vno)]
                    aktif = secili_df.iloc[0].to_dict() if not secili_df.empty else aktif_df.iloc[0].to_dict()
                    vardiya_id = int(aktif['id'])
                else:
                    st.info("Bugün işlem gören vardiya yok.")
            else: # ARŞİV
                arc_date = st.date_input("Arşiv Tarihi", value=get_istanbul_time())
                gecmis_df = db.get_gunluk_vardiyalar(engine, str(arc_date)) 
                gecmis_df = gecmis_df[gecmis_df['durum'] == 'KAPALI']
                if not gecmis_df.empty:
                    arc_options = [f"📦 {row['makina_no']} - V{row['vardiya_no']} (ID: {row['id']})" for _, row in gecmis_df.iterrows()]
                    selected_arc = st.selectbox("O Günün Vardiyaları", arc_options)
                    vardiya_id = int(selected_arc.split("ID: ")[1].replace(")", ""))
                    with engine.connect() as conn:
                        aktif = db._read(conn, "SELECT * FROM map_vardiya WHERE id=:id", {"id": vardiya_id}).iloc[0].to_dict()
                else:
                    st.error("Seçilen tarihte kapalı vardiya bulunamadı.")

        # 4. AKTİF VARDİYA VERİLERİNİ ÇEK (ONE-TIME)
        if vardiya_id:
            st.session_state.map_aktif_vardiya_id = vardiya_id
            with engine.connect() as conn:
                df_zaman = db._read(conn, "SELECT * FROM map_zaman_cizelgesi WHERE vardiya_id=:v", {"v": vardiya_id})
                df_fire = db._read(conn, "SELECT * FROM map_fire_kaydi WHERE vardiya_id=:v", {"v": vardiya_id})
                df_bobin = db._read(conn, "SELECT * FROM map_bobin_kaydi WHERE vardiya_id=:v", {"v": vardiya_id})
                df_vardiya_one = db._read(conn, "SELECT * FROM map_vardiya WHERE id=:id", {"id": vardiya_id})
        else:
            df_zaman = df_fire = df_bobin = df_vardiya_one = None

        # 5. UI LAYOUT (STABLE CONTAINERS)
        if mode == "Bugün" and aktif_sayisi > 1:
            st.write("### 🕹️ Hızlı Makine Geçişi")
            m_cols = st.columns(min(aktif_sayisi, 4))
            for i, (_, row) in enumerate(aktif_df.iterrows()):
                m_no, v_no = row['makina_no'], row['vardiya_no']
                lbl = f"{'🟢' if row['durum'] == 'ACIK' else '🔴'} {m_no} (V{v_no})"
                is_act = (lbl == st.session_state.map_selected_makina_full)
                if m_cols[i % 4].button(f"{'✅' if is_act else lbl[0]} {m_no}", key=f"sw_{row['id']}", type="primary" if is_act else "secondary", use_container_width=True):
                    st.session_state.map_selected_makina_full = lbl; st.rerun()
            st.divider()

        # 6. TABS
        tab_vrd, tab_ctrl, tab_rpr = st.tabs(["🟢 Vardiya", "🕹️ Kontrol Merkezi", "📊 Rapor"])

        with tab_vrd:
            _tab_vardiya(engine, aktif, df_aktif_vardiyalar=all_active_df)

        with tab_ctrl:
            if not vardiya_id: st.warning("⚠️ Önce Vardiya Tabından yeni bir vardiya başlatın.")
            else: _tab_kontrol_merkezi(engine, int(vardiya_id), df_vardiya=df_vardiya_one, df_zaman=df_zaman, df_fire=df_fire, df_bobin=df_bobin)

        with tab_rpr:
            if not vardiya_id: st.warning("⚠️ Analiz için aktif bir vardiya olmalıdır.")
            else: _tab_rapor(engine, int(vardiya_id), df_vardiya=df_vardiya_one, df_zaman=df_zaman, df_fire=df_fire)
                    
    except Exception as e:
        st.error(f"🚨 **MODÜL HATASI:** {str(e)}")
        st.exception(e)
    
    # v4.0.6: GİZLİ DİYAGNOSTİK PANELİ (Sadece Hata Ayıklama İçin)
    with st.expander("🛠️ Sistem Diyagnostik (Admin Mode)", expanded=False):
        st.write("Veritabanındaki Son 5 Vardiya Kaydı (Ham Veri):")
        try:
            with engine.connect() as conn:
                raw_df = pd.read_sql("SELECT * FROM map_vardiya ORDER BY id DESC LIMIT 5", conn)
                st.dataframe(raw_df, use_container_width=True)
        except Exception as deb_e:
            st.error(f"Diyagnostik Hatası: {deb_e}")
