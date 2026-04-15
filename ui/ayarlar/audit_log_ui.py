import streamlit as st
import pandas as pd
from sqlalchemy import text
import json
from logic.auth_logic import kullanici_yetkisi_var_mi
from logic.error_handler import handle_exception

def _audit_render_activity_tab(engine):
    """Aktivite ve Güvenlik sekmesini (Filtreler ve log listesi) render eder."""
    st.info("💡 Sayfa gezintileri, veri güncellemeleri ve güvenlik olayları takip edilir.")
    c1, c2 = st.columns(2)
    types = ["NAVIGASYON", "OTURUM_ACILDI", "VERI_GUNCELLEME", "VERI_EKLEME", "GIRIS_BASARISIZ", "ERISIM_REDDEDILDI"]
    l_types = c1.multiselect("Olay Tipi", types, key="audit_multis")
    days = c2.slider("Son Kaç Gün?", 1, 30, 7, key="audit_slider")
    
    try:
        is_pg = engine.dialect.name == 'postgresql'
        t_filter = f"zaman >= CURRENT_TIMESTAMP - INTERVAL '{days} days'" if is_pg else f"zaman >= datetime('now', '-{days} days')"
        tip_filter, params = ("", {})
        if l_types:
            tip_filter = f"AND islem_tipi IN ({', '.join([f':t{i}' for i in range(len(l_types))])})"
            params = {f"t{i}": v for i, v in enumerate(l_types)}
        
        with engine.connect() as conn:
            df = pd.read_sql(text(f"SELECT * FROM sistem_loglari WHERE {t_filter} {tip_filter} ORDER BY zaman DESC LIMIT 200"), conn, params=params)
        
        if df.empty: st.warning("Kayıt bulunamadı.")
        else:
            st.caption(f"{len(df)} kayıt listeleniyor")
            for _, row in df.iterrows():
                icon = "🧭" if row.get('islem_tipi') == "NAVIGASYON" else "🔒"
                det = str(row.get('detay', ''))
                with st.expander(f"{icon} [{row.get('zaman', '?')}] {row.get('islem_tipi', '?')} | {det[:60]}..."):
                    c1, c2 = st.columns([2, 1])
                    c1.markdown(f"**📍 Modül:** `{row.get('modul', '-')}`\n**👤 Detay:** {det}")
                    c2.markdown(f"**🌐 IP:** `{row.get('ip_adresi', '-')}`\n📱 Cihaz: {row.get('cihaz_bilgisi', '-')}")
                    if row.get('detay_json'): st.divider(); st.caption("📋 Detay (JSON)"); st.json(row['detay_json'])
    except Exception as e: handle_exception(e, modul="AUDIT_LOG_UI", tip="UI")

def _audit_process_cloud_sync(engine):
    """Bulut (Supabase) loglarını yerel veritabanına aktarır."""
    with st.spinner("Bulut bağlantısı (Supabase) kuruluyor..."):
        try:
            from database.connection import get_engine; import os
            c_url = st.secrets.get("database", {}).get("url") or os.getenv("SUPABASE_DB_URL")
            r_eng = create_engine(c_url) if (c_url and "supabase" in c_url) else engine
            with r_eng.connect() as conn: df = pd.read_sql(text("SELECT * FROM hata_loglari ORDER BY zaman DESC LIMIT 200"), conn)
            with get_engine().begin() as l_conn:
                for _, r in df.iterrows():
                    l_conn.execute(text("INSERT INTO hata_loglari (hata_kodu, seviye, modul, fonksiyon, hata_mesaji, stack_trace, context_data, zaman) SELECT :k, :s, :m, :f, :msg, :st, :ctx, :z WHERE NOT EXISTS (SELECT 1 FROM hata_loglari WHERE hata_kodu = :k)"),
                        {"k": r['hata_kodu'], "s": r['seviye'], "m": r['modul'], "f": r['fonksiyon'], "msg": r['hata_mesaji'], "st": r['stack_trace'], "ctx": r['context_data'], "z": r['zaman']})
            st.success(f"✅ {len(df)} kayıt senkronize edildi."); st.rerun()
        except Exception as e: st.error(f"⚠️ Hata: {e}")

def _audit_render_error_item(engine, row, idx):
    """Tekil hata öğesini render eder."""
    fixed = int(row.get('is_fixed', 0)) == 1
    icon = "✅" if fixed else ("🔴" if row.get('seviye') == 'CRITICAL' else "🟡")
    with st.expander(f"{icon} [{row.get('hata_kodu', '?')}] {row.get('modul', '?')} | {str(row.get('hata_mesaji', ''))[:80]}", expanded=(idx == 0 and not fixed)):
        c1, c2 = st.columns([2, 1])
        c1.markdown(f"**Modül/Fonksiyon:** `{row.get('modul', '-')}` / `{row.get('fonksiyon', '-')}`\n**Zaman:** `{row.get('zaman', '-')}`")
        c2.markdown(f"**Seviye:** `{row.get('seviye', '-')}`")
        if row.get('ai_diagnosis'): st.info(str(row['ai_diagnosis']))
        with st.container(border=True): st.caption("🔍 Stack Trace"); st.code(str(row.get('stack_trace', '')), language="python")
        if row.get('context_data'):
            with st.expander("📦 Hata Anındaki Veri"): st.json(row['context_data'])
        btn_txt = "✅ Çözüldü İşaretle" if not fixed else "↩️ Yeniden Aç"
        if st.button(btn_txt, key=f"f_{row.get('hata_kodu', idx)}", type="primary" if not fixed else "secondary"):
            try:
                with engine.begin() as conn: conn.execute(text("UPDATE hata_loglari SET is_fixed=:f WHERE hata_kodu=:k"), {"f": 0 if fixed else 1, "k": row['hata_kodu']})
                st.toast("✅ Güncellendi!"); st.rerun()
            except Exception as e: st.error(f"Hata: {e}")

def _audit_render_error_tab(engine):
    """Teknik Hatalar sekmesini render eder."""
    st.subheader("🚩 AI Destekli Hata Analiz Paneli")
    if st.button("🔄 Bulut Loglarını Senkronize Et", width="stretch"): _audit_process_cloud_sync(engine)
    try:
        with engine.connect() as conn: df = pd.read_sql(text("SELECT * FROM hata_loglari ORDER BY zaman DESC LIMIT 100"), conn)
        if df.empty: st.success("🤖 Hata yok."); return
        m1, m2, m3 = st.columns(3); m1.metric("Toplam", len(df)); m2.metric("✅ Çözüldü", int(df['is_fixed'].sum())); m3.metric("🔥 Kritik", len(df[df['seviye'] == 'CRITICAL']))
        st.divider(); flt = st.radio("Filtrele", ["Tümü", "Açık", "Çözüldü"], horizontal=True)
        for i, row in df.iterrows():
            is_f = int(row.get('is_fixed', 0)) == 1
            if (flt == "Açık" and is_f) or (flt == "Çözüldü" and not is_f): continue
            _audit_render_error_item(engine, row, i)
    except Exception as e: st.error(f"Hata: {e}")

def _render_bulut_analiz(engine):
    """☁️ Supabase → yerel JSONL sync + sürekli analiz paneli."""
    from logic.hata_sync import (bulut_hatalari_indir, son_sync_bilgisi, yerel_hatalari_oku, yerel_dosya_listesi, hata_istatistikleri)
    st.subheader("☁️ Bulut Hata Analiz Merkezi")
    s_info = son_sync_bilgisi(); c1, c2, c3 = st.columns([2, 2, 1])
    if s_info["zaman"]: c1.metric("Son Sync", s_info["zaman"][:16].replace("T", " ")); c2.caption(f"Not: {s_info['not']}")
    else: c1.warning("Henüz sync yapılmadı")
    if c3.button("🔄 Şimdi Sync Et", type="primary", width="stretch", key="btn_bulut_sync"):
        with st.spinner("İndiriliyor..."): _, msg = bulut_hatalari_indir(engine)
        st.toast(msg); st.rerun()
    if st.toggle("⚡ Otomatik Yenile (60 sn)", key="auto_yenile_toggle"):
        try:
             import streamlit as _st
             if hasattr(_st, "fragment"): _otomatik_sync_fragment(engine); return
        except Exception: pass
    df = yerel_hatalari_oku()
    if df.empty: st.info("Yerel kayıt yok."); return
    st.divider(); stats = hata_istatistikleri(df); m1, m2, m3, m4 = st.columns(4); m1.metric("📦 Toplam", stats.get("toplam", 0)); m2.metric("✅ Çözüldü", stats.get("cozuldu", 0)); m3.metric("🔥 Kritik", stats.get("kritik", 0)); m4.metric("🟡 Açık", stats.get("toplam", 0) - stats.get("cozuldu", 0))
    st.divider(); cg1, cg2 = st.columns(2)
    with cg1: st.markdown("**📊 Modül Dağılımı**"); st.bar_chart(pd.Series(stats.get("modul_dagilimi", {})))
    with cg2: st.markdown("**📅 Trend**"); st.bar_chart(pd.Series(stats.get("gun_dagilimi", {})))
    st.dataframe(df[["zaman", "hata_kodu", "seviye", "modul", "hata_mesaji", "is_fixed"]].head(50), width="stretch", hide_index=True, column_config={"is_fixed": st.column_config.CheckboxColumn("Çözüldü"), "hata_mesaji": st.column_config.TextColumn("Hata Mesajı", width="large")})

def render_audit_log_module(engine):
    """Audit Log Modülü Orkestratörü (Anayasa Madde 3 Uyumlu)."""
    st.header("🛡️ Sistem Günlükleri & Analiz")
    t1, t2, t3 = st.tabs(["🔒 Aktivite & Güvenlik", "🛠️ Teknik Hatalar", "☁️ Bulut Analiz"])
    with t1: _audit_render_activity_tab(engine)
    with t2: _audit_render_error_tab(engine)
    with t3: _render_bulut_analiz(engine)

def _otomatik_sync_fragment(engine):
    """Fragment ile otomatik yenileme."""
    try:
        @st.fragment(run_every=60)
        def _yukleme():
            from logic.hata_sync import bulut_hatalari_indir, son_sync_bilgisi
            _, msg = bulut_hatalari_indir(engine); info = son_sync_bilgisi()
            st.caption(f"🔄 Son: {info['zaman'][:16] if info['zaman'] else '—'} | {msg}")
        _yukleme()
    except Exception: pass

if __name__ == "__main__":
    from database.connection import get_engine; render_audit_log_module(get_engine())
