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

    tab_audit, tab_errors, tab_bulut = st.tabs([
        "🔒 Aktivite & Güvenlik",
        "🛠️ Teknik Hatalar (Error Log)",
        "☁️ Bulut Analiz"
    ])

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

    # --- TAB 3: BULUT ANALİZ ---
    with tab_bulut:
        _render_bulut_analiz(engine)


def _render_bulut_analiz(engine):
    """☁️ Supabase → yerel JSONL sync + sürekli analiz paneli."""
    from logic.hata_sync import (
        bulut_hatalari_indir, son_sync_bilgisi,
        yerel_hatalari_oku, yerel_dosya_listesi, hata_istatistikleri
    )

    st.subheader("☁️ Bulut Hata Analiz Merkezi")

    # --- Sync Kontrol Paneli ---
    sync_info = son_sync_bilgisi()
    c1, c2, c3 = st.columns([2, 2, 1])
    if sync_info["zaman"]:
        c1.metric("Son Sync", sync_info["zaman"][:16].replace("T", " "))
        c2.caption(f"Not: {sync_info['not']}")
    else:
        c1.warning("Henüz sync yapılmadı")

    if c3.button("🔄 Şimdi Sync Et", type="primary", use_container_width=True, key="btn_bulut_sync"):
        with st.spinner("Supabase'den indiriliyor..."):
            sayi, mesaj = bulut_hatalari_indir(engine)
        st.toast(mesaj)
        st.rerun()

    # Otomatik yenileme (Streamlit 1.33+)
    otomatik = st.toggle("⚡ Otomatik Yenile (60 sn)", key="auto_yenile_toggle")
    if otomatik:
        try:
            st.write("")
            # st.fragment ile run_every desteği (1.33+)
            import streamlit as _st
            if hasattr(_st, "fragment"):
                st.info("⚡ Otomatik yenileme aktif. Sayfa 60 saniyede bir güncellenir.")
                _otomatik_sync_fragment(engine)
                return
        except Exception:
            pass
        # Fallback: manuel bildirim
        st.info("⚡ Otomatik yenileme: sayfayı manuel yenileyin veya tekrar tıklayın.")

    st.divider()

    # --- Yerel Veriden Analiz ---
    df = yerel_hatalari_oku()
    if df.empty:
        st.info("Yerel dizinde henüz kayıt yok. Sync Et butonuna basın.")
        return

    stats = hata_istatistikleri(df)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 Toplam Hata", stats.get("toplam", 0))
    m2.metric("✅ Çözüldü", stats.get("cozuldu", 0))
    m3.metric("🔥 Kritik", stats.get("kritik", 0))
    acik = stats.get("toplam", 0) - stats.get("cozuldu", 0)
    m4.metric("🟡 Açık", acik)

    st.divider()

    # Grafikler
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("**📊 Modül Bazlı Hata Dağılımı**")
        modul_data = stats.get("modul_dagilimi", {})
        if modul_data:
            st.bar_chart(pd.Series(modul_data))
        else:
            st.info("Veri yok")

    with col_g2:
        st.markdown("**📅 Günlük Hata Trendi**")
        gun_data = stats.get("gun_dagilimi", {})
        if gun_data:
            st.bar_chart(pd.Series(gun_data))
        else:
            st.info("Veri yok")

    # Seviye pasta
    seviye_data = stats.get("seviye_dagilimi", {})
    if seviye_data:
        st.markdown("**🎯 Seviye Dağılımı**")
        sv_cols = st.columns(len(seviye_data))
        for i, (sev, say) in enumerate(seviye_data.items()):
            sv_cols[i].metric(sev, say)

    st.divider()

    # Son hatalar tablosu
    st.markdown("**🗂️ Son 50 Hata Kaydı**")
    goster_cols = [c for c in ["zaman", "hata_kodu", "seviye", "modul", "hata_mesaji", "is_fixed"]
                   if c in df.columns]
    st.dataframe(
        df[goster_cols].head(50),
        use_container_width=True, hide_index=True,
        column_config={
            "is_fixed": st.column_config.CheckboxColumn("Çözüldü"),
            "hata_mesaji": st.column_config.TextColumn("Hata Mesajı", width="large"),
        }
    )

    st.divider()

    # Yerel dosya listesi
    with st.expander("📁 Yerel JSONL Dosyaları"):
        dosyalar = yerel_dosya_listesi()
        if dosyalar:
            st.dataframe(pd.DataFrame(dosyalar), use_container_width=True, hide_index=True)
            st.caption("Konum: logs/hata_loglari/")
        else:
            st.info("Henüz dosya yok.")

    # Daemon çalıştırma talimatı
    with st.expander("⚙️ Arka Plan Daemon (Sürekli Sync)"):
        st.markdown("""
**Arka planda sürekli sync için terminalde çalıştırın:**
```bash
# Her 5 dakikada bir (varsayılan)
python scripts/hata_sync_daemon.py

# Her 1 dakikada bir
python scripts/hata_sync_daemon.py --interval 60

# Tek seferlik test
python scripts/hata_sync_daemon.py --once
```
Daemon çalışırken `logs/hata_loglari/` dizini otomatik güncellenir.
Bu sayfayı yenileyerek en güncel verileri görebilirsiniz.
        """)


def _otomatik_sync_fragment(engine):
    """Streamlit 1.33+ fragment ile otomatik yenileme."""
    try:
        @st.fragment(run_every=60)
        def _yukleme():
            from logic.hata_sync import bulut_hatalari_indir, son_sync_bilgisi
            sayi, mesaj = bulut_hatalari_indir(engine)
            info = son_sync_bilgisi()
            st.caption(f"🔄 Son sync: {info['zaman'][:16] if info['zaman'] else '—'} | {mesaj}")
        _yukleme()
    except Exception:
        pass


if __name__ == "__main__":
    from database.connection import get_engine
    render_audit_log_module(get_engine())
