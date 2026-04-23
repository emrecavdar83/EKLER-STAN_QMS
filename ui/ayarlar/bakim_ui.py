import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text
from logic.sosts_bakim import sosts_bakim_calistir, son_bakim_zamani_getir


def _tarama_verileri_cek(engine):
    """Modül, rol ve yetki verilerini çeker. Hata durumunda None döner."""
    try:
        with engine.connect() as conn:
            moduller = pd.read_sql(text("SELECT modul_anahtari, modul_etiketi, zone FROM ayarlar_moduller WHERE aktif=1 ORDER BY sira_no"), conn)
            roller   = pd.read_sql(text("SELECT rol_adi FROM ayarlar_roller WHERE aktif=1 OR aktif IS NULL ORDER BY rol_adi"), conn)
            yetkiler = pd.read_sql(text("SELECT rol_adi, modul_adi, erisim_turu FROM ayarlar_yetkiler"), conn)
        return moduller, roller, yetkiler
    except Exception as e:
        st.error(f"Tarama hatası: {e}")
        return None, None, None


def _eksikleri_hesapla(moduller, roller, yetkiler):
    """Tanımsız modül×rol kombinasyonlarını listeler."""
    yetki_map  = {(r['rol_adi'], r['modul_adi']): r['erisim_turu'] for _, r in yetkiler.iterrows()}
    zone_renk  = {"ops": "🏭", "mgt": "📊", "sys": "⚙️"}
    eksikler   = []
    for _, mod in moduller.iterrows():
        for _, rol in roller.iterrows():
            erisim = yetki_map.get((rol['rol_adi'], mod['modul_anahtari']), "—")
            if erisim in ("Yok", "—", None):
                eksikler.append({"Zone": zone_renk.get(mod['zone'], "?") + " " + (mod['zone'] or "?"),
                                  "Modül": mod['modul_etiketi'], "Anahtar": mod['modul_anahtari'],
                                  "Rol": rol['rol_adi'], "Mevcut": erisim})
    return eksikler


def _eksik_izin_duzenle_ui(engine, moduller, df_eksik):
    """Eksik izinler için filtre + otomatik düzeltme UI'ını render eder."""
    zone_sec = ["Tümü"] + sorted(df_eksik["Zone"].unique().tolist())
    filtre   = st.selectbox("Zone Filtresi", zone_sec, key="tarama_zone_filtre")
    df_goster = df_eksik if filtre == "Tümü" else df_eksik[df_eksik["Zone"] == filtre]
    st.dataframe(df_goster[["Zone", "Modül", "Rol", "Mevcut"]], width="stretch", hide_index=True)
    st.markdown("---\n#### ⚡ Otomatik Düzeltme")
    col_a, col_b = st.columns(2)
    hedef_erisim = col_a.selectbox("Verilecek Yetki Seviyesi", ["Görüntüle", "Düzenle"], key="tarama_erisim_sec")
    hedef_zone   = col_b.selectbox("Sadece Bu Zone İçin Uygula", ["Tümü", "ops", "mgt", "sys"], key="tarama_zone_uygula")
    if not st.button("🔧 Eksik İzinleri Ekle", type="primary", width="stretch", key="btn_eksik_ekle"):
        return
    uygula_df = df_eksik if hedef_zone == "Tümü" else df_eksik[df_eksik["Anahtar"].isin(moduller[moduller["zone"] == hedef_zone]["modul_anahtari"].tolist())]
    try:
        with engine.begin() as conn:
            for _, row in uygula_df.iterrows():
                conn.execute(text("INSERT INTO ayarlar_yetkiler (rol_adi, modul_adi, erisim_turu) SELECT :r, :m, :e WHERE NOT EXISTS (SELECT 1 FROM ayarlar_yetkiler WHERE rol_adi=:r AND modul_adi=:m)"),
                             {"r": row["Rol"], "m": row["Anahtar"], "e": hedef_erisim})
        from logic.zone_yetki import _YETKI_CACHE
        _YETKI_CACHE.clear()
        if 'yetki_haritasi' in st.session_state:
            del st.session_state['yetki_haritasi']
        st.success(f"✅ {len(uygula_df)} izin girişi eklendi. Kullanıcıların yeniden giriş yapması gerekir.")
        st.rerun()
    except Exception as e:
        st.error(f"Düzeltme hatası: {e}")


def _render_modul_erisim_tarayici(engine):
    """Tüm modül × rol kombinasyonlarını tarar, eksik izinleri gösterir ve düzeltir."""
    st.markdown("### 🔍 Modül Erişim Tarayıcısı")
    st.caption("Hangi rolün hangi modüle erişiminin eksik olduğunu keşfeder ve tek tıkla düzeltir.")
    if not st.button("▶️ Taramayı Başlat", type="primary", width="stretch", key="btn_tarama"):
        return
    with st.spinner("Taranıyor..."):
        moduller, roller, yetkiler = _tarama_verileri_cek(engine)
    if moduller is None or moduller.empty or roller.empty:
        if moduller is not None: st.warning("Modül veya rol verisi bulunamadı.")
        return
    eksikler = _eksikleri_hesapla(moduller, roller, yetkiler)
    toplam = len(moduller) * len(roller)
    c1, c2, c3 = st.columns(3)
    c1.metric("Toplam Kombinasyon", toplam)
    c2.metric("✅ Tanımlı", toplam - len(eksikler))
    c3.metric("⚠️ Eksik / Yok", len(eksikler))
    if not eksikler:
        st.success("Tüm modül-rol kombinasyonları tanımlı. Sistem temiz.")
        return
    _eksik_izin_duzenle_ui(engine, moduller, pd.DataFrame(eksikler))


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
    st.divider()
    _render_parameter_editor(engine)

def _render_parameter_editor(engine):
    """Sistem parametrelerini (JSON formatında) düzenleme imkanı sağlar."""
    st.markdown("### ⚙️ Sistem Parametreleri Editörü")
    st.caption("Constants.py içinden taşınan Pozisyon ve Vardiya gibi kritik sabitleri buradan yönetebilirsiniz.")
    
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text("SELECT id, anahtar, deger, aciklama FROM sistem_parametreleri"), conn)
        
        if df.empty:
            st.warning("Veritabanında hiç parametre bulunamadı.")
            return

        edited_df = st.data_editor(
            df, width="stretch", hide_index=True,
            column_config={
                "id": None,
                "anahtar": st.column_config.TextColumn("🔑 Parametre Anahtarı", disabled=True),
                "deger": st.column_config.TextColumn("📄 Değer (JSON/Text)", width="large"),
                "aciklama": st.column_config.TextColumn("📝 Açıklama")
            },
            key="param_editor"
        )

        if st.button("💾 Parametre Değişikliklerini Kaydet", type="primary", width="stretch"):
            # Değişen satırları bul ve güncelle
            import json
            success_count = 0
            with engine.begin() as conn:
                for _, row in edited_df.iterrows():
                    # JSON geçerlilik kontrolü (opsiyonel ama güvenli)
                    try:
                        if row['anahtar'] in ['POSITION_LEVELS', 'VARDIYA_LISTESI']:
                            json.loads(row['deger'])
                        
                        conn.execute(text("""
                            UPDATE sistem_parametreleri SET deger = :d, aciklama = :a 
                            WHERE id = :id
                        """), {"d": row['deger'], "a": row['aciklama'], "id": row['id']})
                        success_count += 1
                    except json.JSONDecodeError:
                        st.error(f"❌ '{row['anahtar']}' için JSON formatı hatalı!")
                    except Exception as e:
                        st.error(f"❌ '{row['anahtar']}' güncellenirken hata: {e}")
            
            if success_count > 0:
                st.success(f"✅ {success_count} parametre başarıyla güncellendi.")
                # Cache temizle
                st.cache_data.clear() 
                st.rerun()
                
    except Exception as e:
        st.error(f"Parametre yükleme hatası: {e}")
