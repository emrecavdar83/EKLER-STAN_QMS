import streamlit as st
import pandas as pd
import json
from sqlalchemy import text
from constants import get_hijyen_sebepleri, get_hijyen_aksiyonlari

def render_hijyen_ayarlari_tab(engine):
    st.subheader("🧼 Hijyen Nedenleri ve Aksiyonları Yönetimi")
    st.info("💡 Buradan Personel Hijyen modülündeki alt sebep (örn: İzin türleri) ve aksiyon seçeneklerini koda dokunmadan yönetebilirsiniz.")

    # 1. Mevcut parametreleri çek (DB'den taze veya cache)
    try:
        sebepler = get_hijyen_sebepleri()
        aksiyonlar = get_hijyen_aksiyonlari()
    except Exception as e:
        st.error(f"Parametreler yüklenirken hata oluştu: {e}")
        return

    # 2. Kategori Seçimi (Ana Durumlar)
    kategoriler = ["Gelmedi", "Sağlık Riski", "Hijyen Uygunsuzluk"]
    kat_sec = st.selectbox("Düzenlenecek Durum Kategorisini Seçiniz", kategoriler)

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### 📋 Nedenler / Alt Sebepler ({kat_sec})")
        st.caption("Personel bu durumdayken seçilebilecek açıklama listesi. İlk sıradaki 'Seçiniz...' otomatik eklenir.")
        
        # Kategoriye ait mevcut sebepleri al (Seçiniz... varsa listeden gizleyelim ki kullanıcı düzenlemesin, kaydederken ekleriz)
        mevcut_sebepler = sebepler.get(kat_sec, [])
        sebepler_filtreli = [s for s in mevcut_sebepler if s != "Seçiniz..."]
        
        df_sebepler = pd.DataFrame({"Neden": sebepler_filtreli})
        edited_sebepler = st.data_editor(
            df_sebepler,
            num_rows="dynamic",
            width="stretch",
            column_config={"Neden": st.column_config.TextColumn("Detaylı Sebep Açıklaması", required=True)},
            key=f"ed_sebepler_{kat_sec}"
        )

    with col2:
        st.markdown(f"### ⚡ Aksiyonlar ({kat_sec})")
        st.caption("Bu durum tespit edildiğinde alınabilecek aksiyon listesi.")
        
        mevcut_aksiyonlar = aksiyonlar.get(kat_sec, [])
        df_aksiyonlar = pd.DataFrame({"Aksiyon": mevcut_aksiyonlar})
        edited_aksiyonlar = st.data_editor(
            df_aksiyonlar,
            num_rows="dynamic",
            width="stretch",
            column_config={"Aksiyon": st.column_config.TextColumn("Aksiyon Açıklaması", required=True)},
            key=f"ed_aksiyonlar_{kat_sec}"
        )

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button(f"💾 {kat_sec.upper()} PARAMETRELERİNİ KAYDET", type="primary", use_container_width=True):
        # Boşlukları ve NaN değerleri temizle
        yeni_sebepler_list = edited_sebepler["Neden"].dropna().astype(str).str.strip().tolist()
        yeni_sebepler_list = [s for s in yeni_sebepler_list if s and s != "Seçiniz..."]
        # "Seçiniz..." ibaresini her zaman en başa yerleştir
        yeni_sebepler_list = ["Seçiniz..."] + yeni_sebepler_list

        yeni_aksiyonlar_list = edited_aksiyonlar["Aksiyon"].dropna().astype(str).str.strip().tolist()
        yeni_aksiyonlar_list = [a for a in yeni_aksiyonlar_list if a]

        # Ana verileri kopyala ve güncelle
        guncel_sebepler = {k: list(v) for k, v in sebepler.items()}
        guncel_aksiyonlar = {k: list(v) for k, v in aksiyonlar.items()}

        guncel_sebepler[kat_sec] = yeni_sebepler_list
        guncel_aksiyonlar[kat_sec] = yeni_aksiyonlar_list

        # DB'ye yaz
        try:
            with engine.begin() as conn:
                conn.execute(text("""
                    UPDATE sistem_parametreleri 
                    SET deger = :val 
                    WHERE anahtar = 'HIJYEN_SEBEPLERI'
                """), {"val": json.dumps(guncel_sebepler, ensure_ascii=False)})

                conn.execute(text("""
                    UPDATE sistem_parametreleri 
                    SET deger = :val 
                    WHERE anahtar = 'HIJYEN_AKSIYONLARI'
                """), {"val": json.dumps(guncel_aksiyonlar, ensure_ascii=False)})

            st.toast(f"✅ {kat_sec} parametreleri başarıyla güncellendi!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Kayıt sırasında hata oluştu: {e}")
