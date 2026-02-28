import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import time, pytz

from database.connection import get_engine
from logic.data_fetcher import run_query
from logic.auth_logic import kullanici_yetkisi_var_mi

engine = get_engine()

def get_istanbul_time():
    now = datetime.now(pytz.timezone('Europe/Istanbul')) \
        if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()
    return now.replace(microsecond=0)

def _hijyen_personel_listesi(engine):
    """Sistemdeki aktif personel listesini döndürür."""
    p_list = pd.read_sql("""
        SELECT p.ad_soyad,
               COALESCE(d.bolum_adi, 'Tanımsız') as bolum,
               p.vardiya,
               p.durum
        FROM personel p
        LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
        WHERE p.ad_soyad IS NOT NULL
    """, engine)
    p_list.columns = ["Ad_Soyad", "Bolum", "Vardiya", "Durum"]
    
    if not p_list.empty:
        p_list['Durum'] = p_list['Durum'].astype(str).str.strip().str.upper()
        p_list['Vardiya'] = p_list['Vardiya'].astype(str).str.strip()
        p_list['Bolum'] = p_list['Bolum'].astype(str).str.strip()
        p_list = p_list[p_list['Durum'] == "AKTİF"]
        
    return p_list

def _hijyen_tablo_hazirla(personel_isimleri, b_sec):
    """Session state'deki hijyen tablosunu hazırlar/günceller."""
    if 'hijyen_tablo' not in st.session_state or st.session_state.get('son_bolum') != b_sec:
         st.session_state.hijyen_tablo = pd.DataFrame({
            "Personel Adı": personel_isimleri,
            "Durum": "Sorun Yok"
        })
         st.session_state.son_bolum = b_sec
    return st.session_state.hijyen_tablo

def _hijyen_detay_formu(df_sonuc):
    """Sorunlu personel için sebep/aksiyon formunu çizer."""
    sebepler = {
        "Gelmedi": ["Seçiniz...", "Yıllık İzin", "Raporlu", "Habersiz Gelmedi", "Ücretsiz İzin"],
        "Sağlık Riski": ["Seçiniz...", "Ateş", "İshal", "Öksürük", "Açık Yara", "Bulaşıcı Şüphe"],
        "Hijyen Uygunsuzluk": ["Seçiniz...", "Kirli Önlük", "Sakal Tıraşı", "Bone/Maske Eksik", "Yasaklı Takı"]
    }
    aksiyonlar = {
        "Gelmedi": ["İK Bilgilendirildi", "Tutanak Tutuldu", "Bilgi Dahilinde"],
        "Sağlık Riski": ["Üretim Md. Bilgi Verildi", "Eve Gönderildi", "Revire Yönlendirildi", "Maskeli Çalışıyor"],
        "Hijyen Uygunsuzluk": ["Personel Uyarıldı", "Uygunsuzluk Giderildi", "Eğitim Verildi"]
    }
    
    sorunlu_personel = df_sonuc[df_sonuc["Durum"] != "Sorun Yok"]
    detaylar_dict = {}

    if not sorunlu_personel.empty:
        st.divider()
        st.subheader("📝 Tespit Detayı ve Aksiyon")
        cols = st.columns(3)

        for i, (idx, row) in enumerate(sorunlu_personel.iterrows()):
            p_adi = row["Personel Adı"]
            p_durum = row["Durum"]

            with cols[i % 3]:
                with st.container(border=True):
                    st.write(f"**{p_adi}**")
                    sebep = st.selectbox(f"Neden?", sebepler[p_durum], key=f"s_{p_adi}")
                    aksiyon = st.selectbox(f"Aksiyon?", aksiyonlar[p_durum], key=f"a_{p_adi}")
                    detaylar_dict[p_adi] = {"sebep": sebep, "aksiyon": aksiyon}
                    
    return detaylar_dict

def _hijyen_kaydet(df_sonuc, detaylar_dict, v_sec, b_sec, guvenli_coklu_kayit_ekle):
    """Hijyen kayıtlarını doğrular ve DB'ye yazar."""
    kayit_listesi = []
    valid = True

    for _, row in df_sonuc.iterrows():
        p_adi = row["Personel Adı"]
        p_durum = row["Durum"]
        sebep, aksiyon = "-", "-"

        if p_durum != "Sorun Yok":
            det = detaylar_dict.get(p_adi)
            if det and "Seçiniz" not in det["sebep"]:
                sebep, aksiyon = det["sebep"], det["aksiyon"]
            else:
                valid = False; break

        # guvenli_coklu_kayit_ekle list of values beklediği için list oluşturuyoruz
        # Sıralama: tarih, saat, kullanici, vardiya, bolum, personel, durum, sebep, aksiyon
        kayit_listesi.append([
            str(get_istanbul_time().date()),
            get_istanbul_time().strftime("%H:%M"),
            st.session_state.user,
            v_sec, b_sec,
            p_adi, p_durum,
            sebep, aksiyon
        ])

    if valid:
        if guvenli_coklu_kayit_ekle("Hijyen_Kontrol_Kayitlari", kayit_listesi):
            st.success("✅ Veritabanına kaydedildi!"); time.sleep(1); st.rerun()
        else:
            st.error("❌ Kayıt sırasında hata oluştu.")
    else: 
        st.error("Lütfen tüm detayları seçiniz!")

def render_hijyen_module(engine, guvenli_coklu_kayit_ekle):
    """Ana orkestratör."""
    if not kullanici_yetkisi_var_mi("🧼 Personel Hijyen", "Görüntüle"):
        st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır."); st.stop()

    st.title("⚡ Akıllı Personel Kontrol Paneli")

    p_list = _hijyen_personel_listesi(engine)

    if not p_list.empty:
        c1, c2 = st.columns(2)
        vardiya_values = [v for v in p_list['Vardiya'].unique() if v and v != 'nan' and v != 'None']
        v_sec = c1.selectbox("Vardiya Seçiniz", sorted(vardiya_values) if vardiya_values else ["GÜNDÜZ VARDİYASI"])
        p_v = p_list[p_list['Vardiya'] == v_sec]

        if not p_v.empty:
            bolum_values = [b for b in p_v['Bolum'].unique() if pd.notna(b)]
            default_bolum_index = 0
            if st.session_state.get('user_bolum'):
                user_bolum = st.session_state.user_bolum
                for idx, b_opt in enumerate(sorted(bolum_values)):
                     if str(user_bolum).upper() in str(b_opt).upper():
                         default_bolum_index = idx
                         break

            b_sec = c2.selectbox("Bölüm Seçiniz", sorted(bolum_values) if bolum_values else ["Tanımsız"], index=default_bolum_index)
            p_b = p_v[p_v['Bolum'] == b_sec]

            if not p_b.empty:
                personel_isimleri = sorted(p_b['Ad_Soyad'].unique())
                hijyen_tablo = _hijyen_tablo_hazirla(personel_isimleri, b_sec)

                df_sonuc = st.data_editor(
                    hijyen_tablo,
                    column_config={
                        "Personel Adı": st.column_config.TextColumn("Personel", disabled=True),
                        "Durum": st.column_config.SelectboxColumn(
                            "Durum Seçin",
                            options=["Sorun Yok", "Gelmedi", "Sağlık Riski", "Hijyen Uygunsuzluk"],
                            required=True
                        )
                    },
                    hide_index=True,
                    key=f"editor_{b_sec}",
                    use_container_width=True
                )

                detaylar_dict = _hijyen_detay_formu(df_sonuc)

                if st.button(f"💾 {b_sec} DENETİMİNİ KAYDET", type="primary", use_container_width=True):
                    _hijyen_kaydet(df_sonuc, detaylar_dict, v_sec, b_sec, guvenli_coklu_kayit_ekle)
            else: st.warning("Bu bölümde personel bulunamadı.")
        else: st.warning("Bu vardiyada personel bulunamadı.")
    else: st.warning("Sistemde aktif personel bulunamadı.")
