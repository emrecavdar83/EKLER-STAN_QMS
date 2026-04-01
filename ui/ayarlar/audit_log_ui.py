import streamlit as st
import pandas as pd
from sqlalchemy import text
import json
from logic.auth_logic import kullanici_yetkisi_var_mi
from logic.error_handler import handle_exception

def render_audit_log_module(engine):
    """Anayasa v4.0.6: Global Activity Tracker. Güvenlik, Navigasyon ve Hata loglarını gösterir."""

    st.header("🛡️ Sistem Günlükleri & Analiz")
    # Yetki kontrolü: Ayarlar modülü zaten sys zone gerektiriyor (zone_gate ile korunuyor)

    tab_audit, tab_errors = st.tabs(["🔒 Aktivite & Güvenlik", "🛠️ Teknik Hatalar (Error Log)"])

    # --- TAB 1: GÜVENLİK VE AKTİVİTE ---
    with tab_audit:
        st.info("💡 Sayfa gezintileri, veri güncellemeleri ve güvenlik olayları takip edilir.")
        col1, col2 = st.columns(2)
        with col1:
            log_tipi = st.multiselect("Olay Tipi", 
                                     ["NAVIGASYON", "OTURUM_ACILDI", "VERI_GUNCELLEME", "VERI_EKLEME", "GIRIS_BASARISIZ", "ERISIM_REDDEDILDI"],
                                     key="audit_multis")
        with col2:
            gun_sayisi = st.slider("Son Kaç Gün?", 1, 30, 7, key="audit_slider")

        try:
            is_pg = engine.dialect.name == 'postgresql'
            if is_pg:
                tarih_filtre = f"zaman >= CURRENT_TIMESTAMP - INTERVAL '{gun_sayisi} days'"
            else:
                tarih_filtre = f"zaman >= datetime('now', '-{gun_sayisi} days')"

            # IN clause: SQLAlchemy 2.x uyumlu dinamik parametre
            if log_tipi:
                placeholders = ", ".join([f":t{i}" for i in range(len(log_tipi))])
                tip_filtre = f"AND islem_tipi IN ({placeholders})"
                tip_params = {f"t{i}": v for i, v in enumerate(log_tipi)}
            else:
                tip_filtre, tip_params = "", {}

            query = f"SELECT * FROM sistem_loglari WHERE {tarih_filtre} {tip_filtre} ORDER BY zaman DESC LIMIT 200"

            with engine.connect() as conn:
                df = pd.read_sql(text(query), conn, params=tip_params)

            if df.empty:
                st.warning("Henüz bir aktivite kaydı bulunamadı.")
            else:
                st.caption(f"{len(df)} kayıt listeleniyor")
                for idx, row in df.iterrows():
                    icon = "🧭" if row.get('islem_tipi') == "NAVIGASYON" else "🔒"
                    detay_str = str(row.get('detay', ''))
                    baslik = detay_str[:60] + ("..." if len(detay_str) > 60 else "")
                    with st.expander(f"{icon} [{row.get('zaman', '?')}] {row.get('islem_tipi', '?')} | {baslik}"):
                        c1, c2 = st.columns([2, 1])
                        c1.markdown(f"**📍 Modül:** `{row.get('modul', '-')}`")
                        c1.markdown(f"**👤 Detay:** {detay_str}")
                        c2.markdown(f"**🌐 IP:** `{row.get('ip_adresi', '-')}`")
                        c2.caption(f"📱 Cihaz: {row.get('cihaz_bilgisi', '-')}")
                        if row.get('detay_json'):
                            st.divider()
                            st.caption("📋 Veri Değişim Detayı (JSON)")
                            st.json(row['detay_json'])
        except Exception as e:
            handle_exception(e, modul="AUDIT_LOG_UI", tip="UI")

    # --- TAB 2: TEKNİK HATALAR (AI-FRIENDLY) ---
    with tab_errors:
        st.subheader("🚩 AI Destekli Hata Analiz Paneli")
        
        # v4.3.8: BULUT SENKRONİZASYON KÖPRÜSÜ
        col_sync, col_status = st.columns([1, 2])
        if col_sync.button("🔄 Bulut Loglarını Senkronize Et", use_container_width=True, help="Buluttaki (Supabase) hataları yerel veritabanına indirir."):
            with st.spinner("Bulut bağlantısı (Supabase) kuruluyor ve loglar aktarılıyor..."):
                try:
                    # v4.4.0: Uzaktan (Remote) Bulut Bağlantısı Kurma Denemesi
                    from database.connection import get_engine
                    import os
                    
                    # Eğer Cloud'daysak ve halihazırda Supabase'e bağlıysak mevcut engine'i kullan
                    # Eğer Lokal'deysek, secrets'tan bulut URL'sini çekip özel bir Bulut Engine'i oluştur
                    cloud_url = st.secrets.get("database", {}).get("url")
                    if not cloud_url:
                        # Fallback: Yerel .streamlit/secrets.toml veya env'den bak
                        cloud_url = os.getenv("SUPABASE_DB_URL")

                    if cloud_url and "supabase" in cloud_url:
                        from sqlalchemy import create_engine
                        remote_eng = create_engine(cloud_url)
                    else:
                        remote_eng = engine # Mevcut olanla devam et

                    with remote_eng.connect() as conn:
                        df_cloud = pd.read_sql(text("SELECT * FROM hata_loglari ORDER BY zaman DESC LIMIT 200"), conn)
                    
                    # 2. Yerel veritabanına yaz (SQLite)
                    local_eng = get_engine() 
                    # ... (Kayıt mantığı aynı kalacak)
                    with local_eng.begin() as local_conn:
                        # Var olan kayıtları ezmeden (INSERT OR IGNORE mantığı) ekle
                        for _, row in df_cloud.iterrows():
                            local_conn.execute(text("""
                                INSERT INTO hata_loglari (hata_kodu, seviye, modul, fonksiyon, hata_mesaji, stack_trace, context_data, zaman)
                                SELECT :k, :s, :m, :f, :msg, :st, :ctx, :z
                                WHERE NOT EXISTS (SELECT 1 FROM hata_loglari WHERE hata_kodu = :k)
                            """), {
                                "k": row['hata_kodu'], "s": row['seviye'], "m": row['modul'], 
                                "f": row['fonksiyon'], "msg": row['hata_mesaji'], "st": row['stack_trace'],
                                "ctx": row['context_data'], "z": row['zaman']
                            })
                    st.success(f"✅ {len(df_cloud)} bulut kaydı yerel veritabanı ile senkronize edildi.")
                except Exception as sync_e:
                    st.error(f"⚠️ Senkronizasyon hatası: {sync_e}")

        st.caption("Sistemde oluşan teknik hatalar, stack trace ve AI çözüm önerileri burada listelenir.")

        try:
            h_query = "SELECT * FROM hata_loglari ORDER BY zaman DESC LIMIT 100"
            with engine.connect() as conn:
                df_h = pd.read_sql(text(h_query), conn)

            if df_h.empty:
                st.success("🤖 Harika! Son zamanlarda sistemde hiç teknik hata oluşmadı.")
            else:
                # Özet metrikler
                toplam = len(df_h)
                cozuldu = int(df_h['is_fixed'].sum()) if 'is_fixed' in df_h.columns else 0
                kritik = len(df_h[df_h['seviye'] == 'CRITICAL']) if 'seviye' in df_h.columns else 0
                mc1, mc2, mc3 = st.columns(3)
                mc1.metric("Toplam Hata", toplam)
                mc2.metric("✅ Çözüldü", cozuldu)
                mc3.metric("🔥 Kritik", kritik)
                st.divider()

                goster_filter = st.radio("Filtrele", ["Tümü", "Açık", "Çözüldü"], horizontal=True, key="hata_filter")

                for idx, row in df_h.iterrows():
                    is_fixed = int(row.get('is_fixed', 0)) == 1
                    if goster_filter == "Açık" and is_fixed: continue
                    if goster_filter == "Çözüldü" and not is_fixed: continue

                    durum_icon = "✅" if is_fixed else ("🔴" if row.get('seviye') == 'CRITICAL' else "🟡")
                    mesaj_k = str(row.get('hata_mesaji', ''))[:80]
                    with st.expander(f"{durum_icon} [{row.get('hata_kodu', '?')}] {row.get('modul', '?')} | {mesaj_k}", expanded=(idx == 0 and not is_fixed)):
                        c1, c2 = st.columns([2, 1])
                        c1.markdown(f"**Modül/Fonksiyon:** `{row.get('modul', '-')}` / `{row.get('fonksiyon', '-')}`")
                        c1.markdown(f"**Zaman:** `{row.get('zaman', '-')}`")
                        c2.markdown(f"**Seviye:** `{row.get('seviye', '-')}`")

                        if row.get('ai_diagnosis'):
                            st.info(str(row['ai_diagnosis']))

                        with st.container(border=True):
                            st.caption("🔍 Stack Trace")
                            st.code(str(row.get('stack_trace', '')), language="python")

                        if row.get('context_data'):
                            with st.expander("📦 Hata Anındaki Veri"):
                                st.json(row['context_data'])

                        # is_fixed toggle
                        if not is_fixed:
                            if st.button("✅ Çözüldü Olarak İşaretle", key=f"fix_{row.get('hata_kodu', idx)}", type="primary"):
                                try:
                                    with engine.begin() as conn:
                                        conn.execute(text("UPDATE hata_loglari SET is_fixed=1 WHERE hata_kodu=:k"), {"k": row['hata_kodu']})
                                    st.toast("✅ Hata çözüldü olarak işaretlendi.")
                                    st.rerun()
                                except Exception as fix_e:
                                    st.error(f"Güncellenemedi: {fix_e}")
                        else:
                            if st.button("↩️ Yeniden Aç", key=f"unfix_{row.get('hata_kodu', idx)}"):
                                try:
                                    with engine.begin() as conn:
                                        conn.execute(text("UPDATE hata_loglari SET is_fixed=0 WHERE hata_kodu=:k"), {"k": row['hata_kodu']})
                                    st.toast("↩️ Hata yeniden açıldı.")
                                    st.rerun()
                                except Exception as fix_e:
                                    st.error(f"Güncellenemedi: {fix_e}")
        except Exception as e:
            st.error(f"Hata logları yüklenemedi: {e}")

if __name__ == "__main__":
    from database.connection import get_engine
    render_audit_log_module(get_engine())
