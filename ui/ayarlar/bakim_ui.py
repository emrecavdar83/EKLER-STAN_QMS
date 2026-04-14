import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from logic.sosts_bakim import sosts_bakim_calistir, son_bakim_zamani_getir


def _render_modul_erisim_tarayici(engine):
    """Tüm modül × rol kombinasyonlarını tarar, eksik izinleri gösterir."""
    st.markdown("### 🔍 Modül Erişim Tarayıcısı")
    st.caption("Hangi rolün hangi modüle erişiminin eksik olduğunu keşfeder ve tek tıkla düzeltir.")

    if not st.button("▶️ Taramayı Başlat", type="primary", width="stretch", key="btn_tarama"):
        return

    with st.spinner("Taranıyor..."):
        try:
            with engine.connect() as conn:
                moduller = pd.read_sql(
                    text("SELECT modul_anahtari, modul_etiketi, zone FROM ayarlar_moduller WHERE aktif=1 ORDER BY sira_no"),
                    conn
                )
                roller = pd.read_sql(
                    text("SELECT rol_adi FROM ayarlar_roller WHERE aktif=1 OR aktif IS NULL ORDER BY rol_adi"),
                    conn
                )
                yetkiler = pd.read_sql(
                    text("SELECT rol_adi, modul_adi, erisim_turu FROM ayarlar_yetkiler"),
                    conn
                )
        except Exception as e:
            st.error(f"Tarama hatası: {e}")
            return

    if moduller.empty or roller.empty:
        st.warning("Modül veya rol verisi bulunamadı.")
        return

    yetki_map = {
        (r['rol_adi'], r['modul_adi']): r['erisim_turu']
        for _, r in yetkiler.iterrows()
    }

    eksikler = []
    zone_renk = {"ops": "🏭", "mgt": "📊", "sys": "⚙️"}

    for _, mod in moduller.iterrows():
        for _, rol in roller.iterrows():
            erisim = yetki_map.get((rol['rol_adi'], mod['modul_anahtari']), "—")
            if erisim in ("Yok", "—", None):
                eksikler.append({
                    "Zone": zone_renk.get(mod['zone'], "?") + " " + (mod['zone'] or "?"),
                    "Modül": mod['modul_etiketi'],
                    "Anahtar": mod['modul_anahtari'],
                    "Rol": rol['rol_adi'],
                    "Mevcut": erisim,
                })

    # Özet metrikler
    toplam = len(moduller) * len(roller)
    eksik_sayi = len(eksikler)
    tamam_sayi = toplam - eksik_sayi
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Kombinasyon", toplam)
    c2.metric("✅ Tanımlı", tamam_sayi)
    c3.metric("⚠️ Eksik / Yok", eksik_sayi)

    if not eksikler:
        st.success("Tüm modül-rol kombinasyonları tanımlı. Sistem temiz.")
        return

    df_eksik = pd.DataFrame(eksikler)

    # Zone filtresi
    zone_secenekleri = ["Tümü"] + sorted(df_eksik["Zone"].unique().tolist())
    filtre_zone = st.selectbox("Zone Filtresi", zone_secenekleri, key="tarama_zone_filtre")
    df_goster = df_eksik if filtre_zone == "Tümü" else df_eksik[df_eksik["Zone"] == filtre_zone]

    st.dataframe(
        df_goster[["Zone", "Modül", "Rol", "Mevcut"]],
        width="stretch", hide_index=True
    )

    st.markdown("---")
    st.markdown("#### ⚡ Otomatik Düzeltme")

    col_a, col_b = st.columns(2)
    hedef_erisim = col_a.selectbox(
        "Verilecek Yetki Seviyesi",
        ["Görüntüle", "Düzenle"],
        key="tarama_erisim_sec"
    )
    hedef_zone = col_b.selectbox(
        "Sadece Bu Zone İçin Uygula",
        ["Tümü"] + ["ops", "mgt", "sys"],
        key="tarama_zone_uygula"
    )

    if st.button("🔧 Eksik İzinleri Ekle", type="primary", width="stretch", key="btn_eksik_ekle"):
        uygula_df = df_eksik.copy()
        if hedef_zone != "Tümü":
            zone_kodu = hedef_zone
            uygula_df = uygula_df[uygula_df["Anahtar"].isin(
                moduller[moduller["zone"] == zone_kodu]["modul_anahtari"].tolist()
            )]

        eklenen = 0
        try:
            with engine.begin() as conn:
                for _, row in uygula_df.iterrows():
                    conn.execute(text("""
                        INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu)
                        SELECT :r, :m, :e
                        WHERE NOT EXISTS (
                            SELECT 1 FROM ayarlar_yetkiler
                            WHERE rol_adi=:r AND modul_adi=:m
                        )
                    """), {"r": row["Rol"], "m": row["Anahtar"], "e": hedef_erisim})
                    eklenen += 1
            # Yetki cache'ini temizle
            from logic.zone_yetki import _YETKI_CACHE
            _YETKI_CACHE.clear()
            if 'yetki_haritasi' in st.session_state:
                del st.session_state['yetki_haritasi']
            st.success(f"✅ {eklenen} izin girişi eklendi. Kullanıcıların yeniden giriş yapması gerekir.")
            st.rerun()
        except Exception as e:
            st.error(f"Düzeltme hatası: {e}")


def render_bakim_tab(engine):
    """Sistem Bakımı ve Manuel Tetikleyiciler Arayüzü."""
    st.subheader("🔧 Sistem Bakım ve Optimizasyon")
    st.write("Aşağıdaki araçlar, sistemin arka plan görevlerini manuel olarak tetiklemenizi sağlar.")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### ❄️ SOSTS (Soğuk Oda Takip Sistemi) Bakımı")
        st.info("Bu işlem; ölçüm planlarını yeniler, geciken ölçümleri tespit eder ve kritik uyarıları hazırlar.")
        
        son_bakim = son_bakim_zamani_getir(engine)
        if son_bakim:
            gecen = datetime.now() - son_bakim
            if gecen.total_seconds() > 86400:  # 24 saat
                st.error(f"⚠️ **KRİTİK:** Son bakım {son_bakim.strftime('%d.%m.%Y %H:%M')} tarihinde yapılmış. 24 saatlik süre aşılmış!")
            else:
                st.success(f"✅ Son bakım zamanı: {son_bakim.strftime('%d.%m.%Y %H:%M')}")
        else:
            st.warning("⚠️ Bakım henüz hiç çalıştırılmadı veya sistem parametresi bulunamadı.")
            
        if st.button("▶️ SOSTS Bakımını Şimdi Çalıştır", type="primary", width="stretch"):
            with st.spinner("Ölçüm planları güncelleniyor ve gecikmeler analiz ediliyor..."):
                res = sosts_bakim_calistir(engine, st.session_state.get('user', 'ADMIN'))
            if res['basarili']:
                st.toast("✅ Bakım başarıyla tamamlandı!", icon="✅")
                st.rerun()
            else:
                st.error(f"❌ Bakım sırasında bir hata oluştu: {res.get('hata')}")

    with col2:
        st.markdown("### 📊 Sistem Durumu")
        if son_bakim:
            st.metric("Son Bakımdan Beri", f"{gecen.seconds // 3600} saat { (gecen.seconds // 60) % 60} dk")
        st.caption("Not: Sayfa yükleme hızını korumak için bu işlemler artık otomatik çalışmamaktadır.")

    st.divider()
    _render_modul_erisim_tarayici(engine)
