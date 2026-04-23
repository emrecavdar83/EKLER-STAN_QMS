import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import time, pytz

from database.connection import get_engine
from logic.data_fetcher import run_query
from logic.auth_logic import kullanici_yetkisi_var_mi
from constants import HIJYEN_OZET_LIMIT

engine = get_engine()

def get_istanbul_time():
    now = datetime.now(pytz.timezone('Europe/Istanbul')) \
        if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()
    return now.replace(microsecond=0)

def _hijyen_personel_listesi(engine):
    """Matris Mimarisi: personeli operasyonel_bolum_id (Saha Gorevi) uzerinden yukler."""
    # v6.8.9: Targeted Source - Hygiene list now pulls from all factory personnel
    p_list = run_query(
        "SELECT p.id as personel_id, p.ad_soyad, "
        "COALESCE(oper_d.ad, ana_d.ad, 'Tanimsiz') as bolum, "
        "COALESCE(p.vardiya, 'GUNDUZ VARDIYASI') as vardiya, "
        "p.durum, p.ikincil_yonetici_id as saha_sorumlusu_id "
        "FROM tum_personel p "
        "LEFT JOIN qms_departmanlar ana_d ON p.qms_departman_id = ana_d.id "
        "LEFT JOIN qms_departmanlar oper_d ON p.operasyonel_bolum_id = oper_d.id "
        "WHERE p.ad_soyad IS NOT NULL"
    )
    p_list.columns = ["PersonelID", "Ad_Soyad", "Bolum", "Vardiya", "Durum", "SahaSorumlusuID"]
    
    if not p_list.empty:
        p_list['Durum'] = p_list['Durum'].astype(str).str.strip().str.upper()
        p_list['Vardiya'] = p_list['Vardiya'].fillna("G\u00dcND\u00dcZ VARD\u0130YASI").astype(str).str.strip()
        p_list['Bolum'] = p_list['Bolum'].fillna("Tan\u0131ms\u0131z").astype(str).str.strip()
        p_list = p_list[p_list['Durum'] == "AKT\u0130F"]
        
    return p_list


def _hijyen_tablo_hazirla(personel_isimleri, b_sec, v_sec):
    """Session state'deki hijyen tablosunu akıllıca hazırlar/günceller."""
    mevcut_isimler = []
    has_unsaved = False
    
    if 'hijyen_tablo' in st.session_state:
        mevcut_isimler = st.session_state.hijyen_tablo["Personel Adı"].tolist()
        if any(st.session_state.hijyen_tablo["Durum"] != "Sorun Yok"):
            has_unsaved = True
            
    if has_unsaved and (st.session_state.get('son_bolum') != b_sec or st.session_state.get('son_vardiya') != v_sec):
        st.warning("⚠️ Önceki seçiminizde kaydedilmemiş değişiklikler var. Bölüm/Vardiya değiştirmeden önce verilerinizi kaydedin.")
        return st.session_state.hijyen_tablo

    state_degisti = (
        'hijyen_tablo' not in st.session_state or 
        st.session_state.get('son_bolum') != b_sec or 
        st.session_state.get('son_vardiya') != v_sec or
        set(mevcut_isimler) != set(personel_isimleri)
    )

    if state_degisti:
        st.session_state.hijyen_tablo = pd.DataFrame({"Personel Adı": personel_isimleri, "Durum": "Sorun Yok"})
        st.session_state.son_bolum = b_sec
        st.session_state.son_vardiya = v_sec
         
    return st.session_state.hijyen_tablo

def _hijyen_detay_formu(df_sonuc, b_sec="", v_sec=""):
    """Sorunlu ayarlar_kullanicilar için sebep/aksiyon formunu çizer."""
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
                    sebep = st.selectbox(f"Neden?", sebepler[p_durum], key=f"s_{b_sec}_{v_sec}_{p_adi}")
                    aksiyon = st.selectbox(f"Aksiyon?", aksiyonlar[p_durum], key=f"a_{b_sec}_{v_sec}_{p_adi}")
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
            st.session_state['_hijyen_flash'] = "✅ Denetim kaydı veritabanına işlendi!"
            st.rerun()
        else:
            st.error("❌ Kayıt sırasında hata oluştu.")
    else: 
        st.error("Lütfen tüm detayları seçiniz!")

def _hijyen_dashboard(engine):
    """Matris bazlı KPI Dashboard: Son 7 gün, bölüm bazında denetim ve uygunsuzluk özeti."""
    st.subheader("📊 Hijyen Dashboard | Son 7 Gün")
    try:
        # v6.4.0: SQLite/PG uyumlu sorgu — tarih filtresi Python tarafında
        df = run_query(
            "SELECT bolum, durum, COUNT(*) as adet, tarih "
            "FROM hijyen_kontrol_kayitlari "
            "GROUP BY bolum, durum, tarih ORDER BY tarih DESC"
        )
        if not df.empty:
            from datetime import date, timedelta
            yedi_gun_once = str(date.today() - timedelta(days=7))
            df = df[df['tarih'] >= yedi_gun_once]

        if df.empty:
            st.info("ℹ️ Son 7 günde hiç hijyen denetim kaydı bulunamadı.")
            return

        toplam = df['adet'].sum()
        sorun_df = df[df['durum'] != 'Sorun Yok']
        sorun_bolumleri = sorun_df['bolum'].nunique()

        k1, k2, k3 = st.columns(3)
        k1.metric("📋 Toplam Denetim", int(toplam))
        k2.metric("⚠️ Uygunsuzluk Bölüm", sorun_bolumleri,
                  delta=f"-{sorun_bolumleri} Kritik" if sorun_bolumleri > 0 else "Temiz",
                  delta_color="inverse")
        k3.metric("✅ Sorunsuz Kayıt", int(df[df['durum'] == 'Sorun Yok']['adet'].sum()))

        st.divider()
        pivot = df.pivot_table(values='adet', index='bolum', columns='durum', aggfunc='sum', fill_value=0)
        st.dataframe(pivot, width="stretch")

        if not sorun_df.empty:
            with st.expander("⚠️ Son Uygunsuzluk Detayları"):
                # v6.4.0: pd.read_sql(engine) pandas 2.0+ uyumsuz - run_query ile degistirildi
                from datetime import date, timedelta
                yedi_gun_once = str(date.today() - timedelta(days=7))
                recent = run_query(
                    "SELECT tarih, saat, bolum, personel, durum, sebep, aksiyon "
                    "FROM hijyen_kontrol_kayitlari "
                    "WHERE durum != 'Sorun Yok' "
                    f"ORDER BY tarih DESC, saat DESC LIMIT {HIJYEN_OZET_LIMIT}"
                )
                if not recent.empty:
                    recent = recent[recent['tarih'] >= yedi_gun_once]
                st.dataframe(recent, width="stretch", hide_index=True)
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="HIJYEN_DASHBOARD", tip="UI")

def render_hijyen_module(engine, guvenli_coklu_kayit_ekle):
    """Ana orkestratör — Matris Mimarisi + 13. Adam Zırhlı."""
    try:
        if not kullanici_yetkisi_var_mi("🧼 Personel Hijyen", "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır."); st.stop()

        st.title("⚡ Akıllı Personel Kontrol Paneli")

        # FLASH MESAJ SİSTEMİ
        if '_hijyen_flash' in st.session_state:
            st.success(st.session_state.pop('_hijyen_flash'))
        h_tabs = ["✅ Günlük Denetim", "📊 Dashboard"]
        h_sec = st.radio("", h_tabs, horizontal=True, label_visibility="collapsed")
        st.markdown("---")

        if h_sec == h_tabs[1]:
            _hijyen_dashboard(engine)
            return

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
                    n_pers = len(p_b)
                    st.info(f"🌐 **Matris:** {b_sec} sahasında **{n_pers} personel** bulunuyor. (Operasyonel Bölüm Bazı)")
                    personel_isimleri = sorted(p_b['Ad_Soyad'].unique())
                    hijyen_tablo = _hijyen_tablo_hazirla(personel_isimleri, b_sec, v_sec)

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
                        key=f"editor_{b_sec}_{v_sec}",
                        width="stretch"
                    )

                    detaylar_dict = _hijyen_detay_formu(df_sonuc, b_sec, v_sec)

                    if st.button(f"💾 {b_sec} DENETİMİNİ KAYDET", type="primary", width="stretch"):
                        _hijyen_kaydet(df_sonuc, detaylar_dict, v_sec, b_sec, guvenli_coklu_kayit_ekle)
                else: st.warning("Bu bölümde ayarlar_kullanicilar bulunamadı.")
            else: st.warning("Bu vardiyada ayarlar_kullanicilar bulunamadı.")
        else: st.warning("Sistemde aktif ayarlar_kullanicilar bulunamadı.")
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="HIJYEN_ORCHESTRATOR", tip="UI")
