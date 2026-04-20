import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pytz, time, os
from sqlalchemy import text

from database.connection import get_engine
from . import map_db as db
from . import map_hesap as hesap
from logic.auth_logic import kullanici_yetkisi_var_mi, audit_log_kaydet
from logic.data_fetcher import veri_getir

# ─── Config (Anayasa: Zero Hardcode) ─────────────────────────────────────────
MAP_MAKINA_LISTESI = ["MAP-01", "MAP-02", "MAP-03"]
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
        .stButton > button { height: 75px !important; font-size: 18px !important; font-weight: bold !important; border-radius: 15px !important; margin-bottom: 12px !important; transition: all 0.3s ease; }
        .stButton > button:active { transform: scale(0.95); }
        [data-testid="stMetricValue"] { font-size: 28px !important; }
        .stTabs [data-baseweb="tab"] { font-size: 18px !important; padding: 10px 20px !important; }
        @media (max-width: 640px) { .stButton > button { height: 65px !important; font-size: 16px !important; } }
        </style>
    """, unsafe_allow_html=True)

def _get_timer_js(start_ts_str, end_ts_str, unique_id):
    """Sayaç için JS kodunu üretir."""
    stop_logic = f'const endTime = new Date("{end_ts_str.replace(" ", "T")}");' if end_ts_str else 'const endTime = null;'
    return f"""
    <script>
    (function() {{
        const startTime = new Date("{start_ts_str.replace(' ', 'T')}"); {stop_logic}
        const el = document.getElementById("{unique_id}");
        function up() {{
            const now = endTime ? endTime : new Date(); const d = Math.floor((now - startTime) / 1000);
            if (d < 0) return;
            const h = Math.floor(d / 3600), m = Math.floor((d % 3600) / 60), s = d % 60;
            el.innerText = h.toString().padStart(2,'0')+":"+m.toString().padStart(2,'0')+":"+s.toString().padStart(2,'0');
            if (!endTime) setTimeout(up, 1000);
        }} up();
    }})();
    </script>"""

def _render_live_timer(label, start_ts_str, end_ts_str=None, status="active"):
    """HTML/JS kullanarak sayfa yenilemeden sayan canlı sayaç."""
    bg = "#d4edda" if status == "active" else "#f8d7da"
    tc = "#155724" if status == "active" else "#721c24"
    bc = "#28a745" if status == "active" else "#dc3545"
    uid = f"t_{int(time.time())}_{label.replace(' ','')}"
    html = f"""<div style="background:{bg}; padding:15px; border-radius:12px; border:2px solid {bc}; text-align:center;">
        <div style="font-size:12px; color:{tc}; font-weight:bold;">{label}</div>
        <div id="{uid}" style="font-size:28px; font-weight:bold; color:{tc};">00:00:00</div>
    </div>""" + _get_timer_js(start_ts_str, end_ts_str, uid)
    st.components.v1.html(html, height=95)

# ─── Session State & Logic ──────────────────────────────────────────────────
def _init_state():
    defaults = {"map_aktif_vardiya_id": None, "map_son_tık_ts": 0, "map_bobin_form_acik_mi": False, "map_fire_form_acik_mi": False}
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

def _is_click_safe():
    now = time.time()
    if now - st.session_state.map_son_tık_ts < 0.4: return False
    st.session_state.map_son_tık_ts = now
    return True

# ─── Tab 1 — Vardiya ──────────────────────────────────────────────────────────
def _map_get_active_info(engine):
    makina = st.session_state.get('map_selected_makina', 'MAP-01')
    return db.get_aktif_vardiya_live(engine, makina)

def _render_vardiya_kapat_panel(engine, aktif):
    with st.expander(f"🔴 {aktif['makina_no']} VARDİYASINI KAPAT"):
        u_f = st.number_input("Final Üretim", 0, 100000, int(aktif['gerceklesen_uretim'] or 0))
        if st.button("EVET, KAPAT", type="primary"):
            db.kapat_vardiya(engine, int(aktif['id']), int(u_f), int(st.session_state.get('user_id', 0)))
            st.session_state.map_aktif_vardiya_id = None
            if 'map_selected_makina_full' in st.session_state:
                 st.session_state.map_selected_makina_full = st.session_state.map_selected_makina_full.replace("🟢", "🔴")
            st.rerun()

def _render_makine_picker(a_df):
    """v6.1.5: Ana alanda MAP makineleri için buton tabanlı seçici.
    Her koşulda çalışır (boş df, eksik sütun güvenli)."""
    lookup = {}
    try:
        if a_df is not None and not a_df.empty and 'makina_no' in a_df.columns:
            tmp = a_df.sort_values('id', ascending=False).drop_duplicates('makina_no') if 'id' in a_df.columns else a_df
            for _, r in tmp.iterrows():
                icon = '🟢' if str(r.get('durum','')) == 'ACIK' else '🔴'
                lookup[str(r['makina_no']).strip().upper()] = f"{icon} {r['makina_no']} (V{r.get('vardiya_no','?')})"
    except Exception:
        lookup = {}
    st.markdown("##### 🏭 Çalışan Makineler")
    cols = st.columns(len(MAP_MAKINA_LISTESI))
    sel_makina = st.session_state.get('map_selected_makina', MAP_MAKINA_LISTESI[0])
    for i, m in enumerate(MAP_MAKINA_LISTESI):
        raw_lbl = lookup.get(m.upper(), f"⚪ {m} (Boş)")
        # v6.1.7: Seçili olanı ikonla belirginleştir
        btn_lbl = f"📍 {raw_lbl}" if sel_makina == m else raw_lbl
        btn_type = "primary" if sel_makina == m else "secondary"
        
        if cols[i].button(btn_lbl, key=f"map_pick_{m}", width="stretch", type=btn_type):
            st.session_state.map_selected_makina = m
            # Sidebar seçimini de senkronize etmek için etiketi temizle
            if 'map_selected_makina_full' in st.session_state:
                del st.session_state['map_selected_makina_full']
            st.rerun()
    
    # v6.1.7: Seçim konfirmasyon paneli
    st.markdown(f"""
        <div style="background-color: #f1f5f9; padding: 10px; border-left: 5px solid #8B0000; border-radius: 5px; margin-bottom: 20px;">
            <span style="color: #64748b; font-weight: 600;">Görüntülenen:</span> 
            <span style="color: #8B0000; font-weight: 800; font-size: 1.1rem;">{sel_makina}</span>
        </div>
    """, unsafe_allow_html=True)
    st.divider()

def _tab_vardiya(engine, aktif=None, df_aktif_vardiyalar=None):
    if df_aktif_vardiyalar is None:
        df_aktif_vardiyalar = db.get_tum_aktif_vardiyalar(engine)
    item = _map_get_active_info(engine)
    if not item:
        st.info("⚪ Aktif vardiya bulunmuyor."); aktif = None
    else:
        aktif = item; st.session_state.map_aktif_vardiya_id = int(aktif['id'])
        if aktif.get('durum') == 'ACIK':
            st.success(f"🟢 **{aktif['makina_no']}** | {aktif['vardiya_no']}. Vardiya")
            st.caption(f"👷 {aktif['operator_adi']} | {aktif['tarih']} {aktif['baslangic_saati']}")
            st.text_area("📝 Notlar", value=aktif.get('notlar','') or "", key=f"not_{aktif['id']}")
            _render_vardiya_kapat_panel(engine, aktif)
        else: st.info(f"🏁 **{aktif['makina_no']} (KAPALI)**")
    bostaki = [m for m in MAP_MAKINA_LISTESI if m.upper() not in [n.strip().upper() for n in df_aktif_vardiyalar['makina_no'].tolist()]]
    if bostaki:
        sel_makina = st.session_state.get('map_selected_makina', MAP_MAKINA_LISTESI[0])
        default_m = sel_makina if sel_makina in bostaki else (aktif['makina_no'] if aktif and aktif['makina_no'] in bostaki else bostaki[0])
        with st.expander("➕ Yeni Makine Başlat", expanded=(not aktif) or (default_m in bostaki)):
            _render_yeni_vardiya_form(engine, bostaki, varsayilan_makina=default_m)

def _map_process_new_shift(engine, makina, vno, op, sef, bes, kas, hiz, selected_urun):
    try:
        vid = db.aç_vardiya(engine, makina, vno, op, int(st.session_state.get('user_id', 0)), sef, bes, kas, hiz, selected_urun)
        db.insert_zaman_kaydi(engine, vid, "CALISIYOR")
        st.session_state.map_aktif_vardiya_id = vid
        st.session_state.map_selected_makina = makina
        _v = st.session_state.get('_fv_yeni_vardiya_form', 0)
        st.session_state['_fv_yeni_vardiya_form'] = _v + 1
        st.success(f"✅ {makina} Başlatıldı!"); st.rerun()
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="MAP_VARD_AC", tip="UI")

def _render_yeni_vardiya_form(engine, bostaki, varsayilan_makina=None):
    _v = st.session_state.get('_fv_yeni_vardiya_form', 0)
    with st.form(f"yeni_vardiya_form_v{_v}"):
        c1, c2 = st.columns(2)
        makina = c1.selectbox("Makina", bostaki, index=bostaki.index(varsayilan_makina) if varsayilan_makina in bostaki else 0)
        vno = c2.selectbox("Vardiya No", [1, 2, 3])
        op = st.text_input("Operatör", value=st.session_state.get('user_fullname', st.session_state.get('user', '')), disabled=True)
        u_df = veri_getir("Ayarlar_Urunler")
        urunler = sorted(u_df['urun_adi'].unique().tolist()) if not u_df.empty else []
        selected_urun = st.selectbox("Ürün", urunler)
        sef = st.text_input("Vardiya Şefi")
        c3, c4, c5 = st.columns(3)
        bes, kas, hiz = c3.number_input("Besleme", 0, 20, 4), c4.number_input("Kasalama", 0, 20, 1), c5.number_input("Hız", 0.1, 20.0, 4.2)
        if st.form_submit_button("🟢 BAŞLAT", type="primary"):
            if not selected_urun: st.error("Ürün seçin!"); return
            _map_process_new_shift(engine, makina, vno, op, sef, bes, kas, hiz, selected_urun)

# ─── Tab 2 — Kontrol Merkezi ────────────────────────────────────────────────
def _tab_kontrol_merkezi(engine, vardiya_id, df_vardiya=None, df_zaman=None, df_fire=None, df_bobin=None):
    if df_vardiya is None:
        with engine.connect() as conn: df_vardiya = db._read(conn, "SELECT * FROM map_vardiya WHERE id=:id", {"id": vardiya_id})
    aktif = df_vardiya.iloc[0].to_dict() if not df_vardiya.empty else None
    if not aktif: st.warning("🚨 Veri yok."); return
    son = (df_zaman.sort_values('id', ascending=False).iloc[0].to_dict() if not (df_zaman is None or df_zaman.empty) else db.get_son_zaman_kaydi(engine, vardiya_id))
    durum = son['durum'] if son and aktif.get('durum') == 'ACIK' else "KAPALI"
    _map_render_status_timers(aktif, son, durum, son.get('neden','') if son else '')
    st.divider()
    l, r = st.columns(2)
    with l: _map_render_production_controls(engine, vardiya_id, aktif, durum)
    with r: _map_render_fire_bobin(engine, vardiya_id)
    st.divider()
    _map_render_admin_panel(engine, vardiya_id, aktif, df_fire)
    with st.expander("🕒 Zaman Çizelgesi"):
        st.dataframe(df_zaman if df_zaman is not None else db.get_zaman_cizelgesi(engine, vardiya_id), width="stretch", hide_index=True)

def _map_render_status_timers(aktif, son, durum, aktif_neden):
    c_s, c_t1, c_t2 = st.columns([2, 1, 1])
    with c_s:
        bg, tc, bc = ("#d4edda","#155724","#28a745") if durum == "CALISIYOR" else (("#f8d7da","#721c24","#dc3545") if durum == "DURUS" else ("#e2e3e5","#383d41","#6c757d"))
        st.markdown(f'<div style="background:{bg}; padding:12px; border-radius:12px; border:2px solid {bc}; height:100px; display:flex; flex-direction:column; justify-content:center;">'
                    f'<h3 style="color:{tc}; margin:0; font-size:20px;">{aktif_neden if durum == "DURUS" else (durum if durum != "CALISIYOR" else "ÜRETİM DEVAM EDİYOR")}</h3>'
                    f'<p style="color:{tc}; margin:0; font-size:14px;">{aktif["operator_adi"] if durum != "KAPALI" else "Vardiya Kapatıldı"}</p></div>', unsafe_allow_html=True)
    with c_t1:
        if son and son.get('baslangic_ts'):
            _render_live_timer("Durum Süresi", son['baslangic_ts'], end_ts_str=son['bitis_ts'] if aktif.get('durum') == 'KAPALI' else None, status="active" if durum == "CALISIYOR" else "idle")
    with c_t2:
        v_bas = f"{aktif['tarih']} {aktif['baslangic_saati']}:00"
        v_end = f"{aktif['tarih']} {aktif['bitis_saati']}:00" if aktif.get('durum') == 'KAPALI' else None
        _render_live_timer("TOPLAM VARDIYA", v_bas, end_ts_str=v_end, status="active")

def _map_render_production_controls(engine, vardiya_id, aktif, durum):
    st.subheader("⚡ Duruş & 📦 Üretim")
    if aktif.get('durum') == "ACIK":
        if durum == "CALISIYOR":
            for i, ned in enumerate(db.get_map_durus_nedenleri(engine)):
                if st.button(f"🔻 {ned}", key=f"d_btn_{i}", width="stretch"):
                    if _is_click_safe(): db.insert_zaman_kaydi(engine, vardiya_id, "DURUS", neden=ned); st.rerun()
        else:
            if st.button("🟢 İŞE BAŞLA", width="stretch", type="primary"):
                if _is_click_safe(): db.insert_zaman_kaydi(engine, vardiya_id, "CALISIYOR"); st.rerun()
    with st.expander("➕ Üretim Ekle", expanded=True):
        add = st.number_input("Adet", 0, 10000, 100, step=10)
        if st.button("➕ KAYDET", type="primary"):
            db.update_kumulatif_uretim(engine, vardiya_id, add); st.toast(f"✅ {add} eklendi!"); st.rerun()
        st.caption(f"Güncel: **{aktif['gerceklesen_uretim']}**")

def _map_render_fire_bobin(engine, vardiya_id):
    st.subheader("🔥 Kayıplar & 🎞️ Bobin")
    if st.toggle("🔥 Fire Paneli"):
        with st.container(border=True):
            f_mik = st.number_input("Adet", 1, 1000, 10, key="f_input")
            for i, tip in enumerate(db.get_map_fire_tipleri(engine)):
                if st.button(f"➕ {tip}", key=f"f_type_{i}", width="stretch"):
                    if _is_click_safe(): db.insert_fire(engine, vardiya_id, tip, int(f_mik)); st.toast(f"✅ {f_mik} {tip} eklendi!"); st.rerun()
    if st.toggle("🎞️ Bobin Değişim"):
        _v = st.session_state.get('_fv_bobin_f', 0)
        with st.form(f"bobin_f_v{_v}"):
            lot = st.text_input("LOT")
            tip = st.selectbox("Film", ["Üst Film", "Alt Film"])
            cat1, cat2 = st.columns(2)
            bas, bit = cat1.number_input("Yeni (KG)", 0.0, 100.0, 25.0), cat2.number_input("Eski (KG)", 0.0, 100.0, 0.0)
            if st.form_submit_button("✅ KAYDET"):
                db.insert_bobin(engine, vardiya_id, lot, tip, bas, bit)
                st.session_state['_fv_bobin_f'] = _v + 1
                st.toast("✅ Kaydedildi!"); st.rerun()

def _map_render_admin_panel(engine, vardiya_id, aktif, df_fire):
    if st.session_state.get('user_rol') == 'ADMIN':
        with st.expander("🛠️ Admin Düzeltme"):
            st.write("### 📦 Üretim Düzeltme")
            c1, c2 = st.columns([1, 2])
            new_t = c1.number_input("Yeni Toplam", 0, 100000, int(aktif['gerceklesen_uretim'] or 0))
            reason = c2.text_input("Neden", key="adj_r")
            if st.button("⚠️ GÜNCELLE") and reason.strip() and _is_click_safe():
                db.set_net_uretim(engine, vardiya_id, new_t); audit_log_kaydet("MAP_ADJ", f"{vardiya_id}:{new_t}"); st.rerun()
            st.write("### 🔥 Fire Düzeltme")
            df_f = df_fire if df_fire is not None else db.get_fire_kayitlari(engine, vardiya_id)
            for _, r in df_f.iterrows():
                with st.container(border=True):
                    fc1, fc2, fc3 = st.columns([2, 1, 1])
                    new_fm = fc1.number_input(f"{r['fire_tipi']}", 0, 10000, int(r['miktar_adet']), key=f"fe_{r['id']}")
                    r_f = fc2.text_input("Neden", key=f"fr_{r['id']}")
                    if fc3.button("💾", key=f"fb_{r['id']}") and r_f.strip() and _is_click_safe():
                        db.set_fire_miktar(engine, r['id'], new_fm); st.rerun()

# ─── Tab 3 — Rapor ───────────────────────────────────────────────────────────
def _map_render_kpi_metrics(ozet, uretim):
    h_f = uretim.get('hiz_farki_pct', 0)
    h_l = f"{'🔼' if h_f > 0 else '🔽' if h_f < 0 else '➖'} {h_f}%"
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Üretim", f"{uretim['gerceklesen_uretim']} pk", f"Hedef: {uretim['teorik_uretim']}")
    c2.metric("OEE (Kul.)", f"%{ozet['kullanilabilirlik_pct']}")
    c3.metric("🔥 Fire", f"%{uretim['fire_pct']}", f"{uretim['fire_adet']} adet")
    c4.metric("🚀 Hız", f"{uretim.get('gercek_hiz', 0)} pk/dk", h_l)
    st.write("---")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("⏱️ Toplam", f"{ozet['toplam_vardiya_dk']} dk")
    s2.metric("🟢 Çalışma", f"{ozet['toplam_calisma_dk']} dk")
    s3.metric("🔴 Duruş", f"{ozet['toplam_durus_dk']} dk")
    s4.metric("☕ Mola", f"{ozet['mola_dk']} dk")

def _tab_rapor(engine, vardiya_id, df_vardiya=None, df_zaman=None, df_fire=None):
    st.subheader("📊 Canlı Vardiya Dashboard")
    ozet = hesap.hesapla_sure_ozeti(engine, vardiya_id, df_zaman=df_zaman, df_vardiya=df_vardiya)
    uretim = hesap.hesapla_uretim(engine, vardiya_id, df_vardiya=df_vardiya, df_fire=df_fire, sure_ozeti=ozet)
    if not ozet or not uretim: st.warning("Hesaplanıyor..."); return
    _map_render_kpi_metrics(ozet, uretim)
    st.divider()
    cl, cr = st.columns(2)
    with cl:
        st.write("**⏱️ Duruş Dağılımı (dk)**")
        df_d = pd.DataFrame(hesap.hesapla_durus_ozeti(engine, vardiya_id, df_zaman=df_zaman))
        if not df_d.empty: st.bar_chart(df_d.set_index('neden')['toplam_dk'])
    with cr:
        st.write("**🔥 Fire Tipleri (adet)**")
        df_f = pd.DataFrame(hesap.hesapla_fire_ozeti(engine, vardiya_id, df_fire=df_fire))
        if not df_f.empty: st.bar_chart(df_f.set_index('fire_tipi')['miktar'])
    st.divider(); _map_render_pdf_trigger(engine, vardiya_id, df_zaman, df_fire)

def _map_render_pdf_trigger(engine, vardiya_id, df_zaman, df_fire):
    try:
        from .map_rapor_pdf import uret_is_raporu_html
        import json
        if st.button("📄 KURUMSAL RAPOR OLUŞTUR", width="stretch"):
            html = uret_is_raporu_html(engine, vardiya_id, df_zaman=df_zaman, df_fire=df_fire)
            if html:
                js = f"<script>var h={json.dumps(html)}; var b=new Blob([h],{{type:'text/html'}}); var u=URL.createObjectURL(b); window.open(u,'_blank');</script>"
                st.components.v1.html(js, height=0); st.success("Rapor açıldı.")
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="MAP_RAPOR", tip="UI")

# ─── Ana Fonksiyon ────────────────────────────────────────────────────────────
def _map_sidebar_section(engine, all_active, bugun):
    with st.sidebar:
        st.header("🏭 Makineler")
        m = st.radio("Mod", ["Bugün", "Arşiv"], horizontal=True)
        v_id, aktif, a_df = None, None, None
        if m == "Bugün":
            a_df = pd.concat([all_active, bugun]).drop_duplicates('id')
            if not a_df.empty:
                a_df = a_df.sort_values('id', ascending=False).drop_duplicates('makina_no').sort_values('makina_no')
                opts = [f"{'🟢' if r['durum']=='ACIK' else '🔴'} {r['makina_no']} (V{r['vardiya_no']})" for _, r in a_df.iterrows()]
                
                # v6.1.6: Seçili makine ismini (örn: MAP-01) etikete çevir (örn: 🟢 MAP-01 (V1))
                curr_m = st.session_state.get('map_selected_makina', MAP_MAKINA_LISTESI[0])
                matching_opts = [o for o in opts if f" {curr_m} (" in o]
                
                if matching_opts:
                    st.session_state.map_selected_makina_full = matching_opts[0]
                elif 'map_selected_makina_full' not in st.session_state or st.session_state.map_selected_makina_full not in opts:
                    st.session_state.map_selected_makina_full = opts[0]
                
                sel = st.selectbox("Makine", opts, index=opts.index(st.session_state.map_selected_makina_full))
                if sel != st.session_state.map_selected_makina_full: 
                    st.session_state.map_selected_makina_full = sel
                    st.session_state.map_selected_makina = sel[2:].split(" (")[0]
                    st.rerun()
                
                m_r = sel[2:].split(" (")[0]; v_n = int(sel.split("(V")[1].replace(")", ""))
                s_df = a_df[(a_df['makina_no'] == m_r) & (a_df['vardiya_no'] == v_n)]
                aktif = s_df.iloc[0].to_dict(); v_id = int(aktif['id'])
        else:
            d = st.date_input("Tarih", value=get_istanbul_time())
            g = db.get_gunluk_vardiyalar(engine, str(d)); g = g[g['durum'] == 'KAPALI']
            if not g.empty:
                sel_arc = st.selectbox("Vardiyalar", [f"📦 {r['makina_no']} - V{r['vardiya_no']} (ID:{r['id']})" for _, r in g.iterrows()])
                v_id = int(sel_arc.split("ID:")[1].replace(")","")); aktif = db.get_vardiya_by_id(engine, v_id)
        return v_id, aktif, a_df

def render_map_module(engine=None):
    """Ana orkestratör (Anayasa Madde 3 Uyumlu)."""
    try:
        if not kullanici_yetkisi_var_mi("📦 MAP Üretim", "Görüntüle"): st.error("🚫 Yetki yok."); st.stop()
        if engine is None: engine = get_engine()
        _init_state(); _inject_custom_css(); st.title("📦 MAP Üretim Takip")
        all_active = db.get_tum_aktif_vardiyalar(engine)
        bugun = db.get_bugunku_vardiyalar(engine)
        v_id, aktif, a_df = _map_sidebar_section(engine, all_active, bugun)
        # v6.1.5: Makine seçim butonları tablardan önce daima görünür.
        picker_df = a_df if (a_df is not None and not a_df.empty) else pd.concat([all_active, bugun], ignore_index=True)
        _render_makine_picker(picker_df)
        # v6.1.4: Tablar daima render edilir — ilk vardiyayı açabilmek için
        t_v, t_c, t_r = st.tabs(["🟢 Vardiya", "🕹️ Kontrol Merkezi", "📊 Rapor"])
        with t_v: _tab_vardiya(engine, aktif, df_aktif_vardiyalar=a_df)
        if v_id:
            with engine.connect() as cn:
                dz, df, dbb, dv = db._read(cn,"SELECT * FROM map_zaman_cizelgesi WHERE vardiya_id=:v",{"v":v_id}), db._read(cn,"SELECT * FROM map_fire_kaydi WHERE vardiya_id=:v",{"v":v_id}), db._read(cn,"SELECT * FROM map_bobin_kaydi WHERE vardiya_id=:v",{"v":v_id}), db._read(cn,"SELECT * FROM map_vardiya WHERE id=:id",{"id":v_id})
            with t_c: _tab_kontrol_merkezi(engine, v_id, df_vardiya=dv, df_zaman=dz, df_fire=df, df_bobin=dbb)
            with t_r: _tab_rapor(engine, v_id, df_vardiya=dv, df_zaman=dz, df_fire=df)
        else:
            with t_c: st.info("ℹ️ Kontrol Merkezi için önce bir vardiya seçin veya başlatın.")
            with t_r: st.info("ℹ️ Rapor için önce bir vardiya seçin veya başlatın.")
        _render_diagnostic(engine)
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="MAP_ORCHESTRATOR", tip="UI")

def _render_diagnostic(engine):
    with st.expander("🛠️ Sistem Diyagnostik (Admin Mode)", expanded=False):
        try:
            with engine.connect() as conn:
                st.dataframe(pd.read_sql("SELECT * FROM map_vardiya ORDER BY id DESC LIMIT 5", conn), width="stretch")
        except Exception: pass
