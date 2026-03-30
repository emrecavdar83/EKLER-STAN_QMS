import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta
import time, os, pytz

from database.connection import get_engine
from logic.data_fetcher import veri_getir, run_query
from logic.auth_logic import kullanici_yetkisi_var_mi, bolum_bazli_urun_filtrele

engine = get_engine()

def get_istanbul_time():
    now = datetime.now(pytz.timezone('Europe/Istanbul')) \
        if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()
    return now.replace(microsecond=0)

def _kpi_urun_sec(u_df):
    """Ürün seçim arayüzü. Seçilen ürünü ve ayarlarını döndürür."""
    c1, c2 = st.columns(2)
    # Sütun isimlerini küçük harfe zorlar (standardizasyon)
    u_df.columns = [c.lower() for c in u_df.columns]
    
    urun_secilen = c1.selectbox("Ürün Seçin", u_df['urun_adi'].unique())
    if not urun_secilen:
        st.warning("Lütfen bir ürün seçiniz.")
        return None, None, None, None

    lot_kpi = c2.text_input("Lot No", placeholder="Üretim Lot No")
    vardiya_kpi = c1.selectbox("Vardiya", ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"], key="kpi_v")
    
    urun_ayar = u_df[u_df['urun_adi'] == urun_secilen].iloc[0]
    return urun_secilen, lot_kpi, vardiya_kpi, urun_ayar

def _kpi_parametre_getir(urun_secilen, urun_ayar):
    """Ürün parametrelerini DB'den çeker."""
    try:
        numune_adet = int(float(urun_ayar.get('numune_sayisi', 1) or 1))
    except:
        numune_adet = 1
    if numune_adet < 1: numune_adet = 1

    # Parametreleri Çek
    params_sql = text("SELECT * FROM urun_parametreleri WHERE urun_adi = :u")
    try:
        params_df = pd.read_sql(params_sql, engine, params={"u": urun_secilen})
    except Exception:
        params_df = pd.DataFrame()

    if params_df.empty:
        # Eğer parametre yoksa eski usül (varsayılan) 3 ölçüm varsayalım
        param_list = [
            {"parametre_adi": urun_ayar.get('olcum1_ad','Ölçüm 1')},
            {"parametre_adi": urun_ayar.get('olcum2_ad','Ölçüm 2')},
            {"parametre_adi": urun_ayar.get('olcum3_ad','Ölçüm 3')}
        ]
    else:
        param_list = params_df.to_dict('records')

    try:
        raf_omru = int(float(urun_ayar.get('raf_omru_gun', 0) or 0))
    except:
        raf_omru = 0
    stt_date = get_istanbul_time().date() + timedelta(days=raf_omru)
    
    return param_list, numune_adet, raf_omru, stt_date

def _kpi_olcum_formu(param_list, numune_adet, stt_date, urun_secilen, raf_omru):
    """Dinamik ölçüm formunu çizer. Ölçüm verilerini döndürür."""
    st.info(f"ℹ {urun_secilen} için Raf Ömrü: {raf_omru} Gün | STT: {stt_date} | Numune Sayısı: {numune_adet}")
    
    with st.form("kpi_form"):
        # 1. STT ve Etiket Kontrolü (Zorunlu)
        st.subheader("✅ Ön Kontroller")
        stt_ok = st.checkbox("Üretim Tarihi ve Son Tüketim Tarihi (STT) Etiket Bilgisi Doğrudur")
        stt_foto = st.file_uploader("📸 STT Etiket Fotoğrafı (Zorunlu)", type=['jpg','png','jpeg'], key="stt_foto_upload")

        st.divider()
        st.subheader(f"📏 Ölçüm Değerleri ({numune_adet} Numune)")

        # Veri Toplama Havuzu
        all_measurements = []
        for i in range(numune_adet):
             with st.container():
                st.markdown(f"**Numune #{i+1}**")
                cols = st.columns(len(param_list))
                sample_data = {}

                for p_idx, param in enumerate(param_list):
                    p_ad = param['parametre_adi']
                    if p_ad:
                        val = cols[p_idx % len(cols)].number_input(
                            f"{p_ad}",
                            key=f"n{i}_p{p_idx}",
                            step=0.1,
                            min_value=0.0
                        )
                        sample_data[p_ad] = val

                all_measurements.append(sample_data)
                st.markdown("---")

        st.subheader("Duyusal Kontrol & Sonuç")
        d1, d2 = st.columns(2)
        tat = d1.selectbox("Tat / Koku", ["Uygun", "Uygun Değil"])
        goruntu = d2.selectbox("Görüntü / Renk", ["Uygun", "Uygun Değil"])
        not_kpi = st.text_area("Kalite Notu / Açıklama")

        submitted = st.form_submit_button("✅ Analizi Kaydet")
        if submitted:
            return {
                "stt_ok": stt_ok,
                "stt_foto": stt_foto,
                "all_measurements": all_measurements,
                "tat": tat,
                "goruntu": goruntu,
                "not_kpi": not_kpi
            }
    return None

def _kpi_kaydet(urun_secilen, lot_kpi, vardiya_kpi,
                stt_date, numune_adet, param_list,
                form_data, guvenli_kayit_ekle):
    """Karar mantığı ve DB kaydı."""
    stt_ok = form_data["stt_ok"]
    stt_foto = form_data["stt_foto"]
    all_measurements = form_data["all_measurements"]
    tat = form_data["tat"]
    goruntu = form_data["goruntu"]
    not_kpi = form_data["not_kpi"]

    if not stt_ok:
        st.error("⛔ Kayıt için STT ve Etiket bilgisini doğrulamalısınız!")
        return
    if not stt_foto:
        st.error("⛔ Kayıt için STT Etiket fotoğrafı yüklemelisiniz!")
        return

    try:
        # Fotografı Diske Kaydet (yedek olarak)
        os.makedirs("data/uploads/kpi", exist_ok=True)
        foto_uzanti = stt_foto.name.split('.')[-1].lower()
        foto_adi = f"stt_{get_istanbul_time().strftime('%Y%m%d_%H%M%S')}.{foto_uzanti}"
        foto_yolu = f"data/uploads/kpi/{foto_adi}"
        foto_bytes = stt_foto.getbuffer()
        
        with open(foto_yolu, "wb") as f:
            f.write(foto_bytes)

        # BRC UYUMLULUK: Fotografı Base64 olarak DB'ye kaydet (kalici kanit - silinemez)
        import base64 as b64lib
        mime = 'image/jpeg' if foto_uzanti in ['jpg', 'jpeg'] else 'image/png'
        foto_b64 = f"data:{mime};base64," + b64lib.b64encode(foto_bytes).decode('utf-8')

        # Karar Mantığı
        karar = "RED"
        if tat == "Uygun" and goruntu == "Uygun":
            karar = "ONAY"

        # İstatistik Hesapla (Eski raporlar için ilk 3 parametre ortalaması)
        avg_val1, avg_val2, avg_val3 = 0.0, 0.0, 0.0
        if len(param_list) > 0:
            p1_name = param_list[0]['parametre_adi']
            if p1_name: avg_val1 = sum([m.get(p1_name, 0) for m in all_measurements]) / numune_adet
        if len(param_list) > 1:
            p2_name = param_list[1]['parametre_adi']
            if p2_name: avg_val2 = sum([m.get(p2_name, 0) for m in all_measurements]) / numune_adet
        if len(param_list) > 2:
            p3_name = param_list[2]['parametre_adi']
            if p3_name: avg_val3 = sum([m.get(p3_name, 0) for m in all_measurements]) / numune_adet

        # Detaylı Veri Stringi
        detay_str = f"STT Onaylandı. "
        for idx, m in enumerate(all_measurements):
            detay_str += f"[N{idx+1}: " + ", ".join([f"{k}={v}" for k,v in m.items()]) + "] "
        final_not = f"{not_kpi} | {detay_str}"

        simdi = get_istanbul_time()
        veri_paketi = [
            str(simdi.date()), simdi.strftime("%H:%M"), vardiya_kpi, urun_secilen,
            "", lot_kpi, str(stt_date), str(numune_adet),
            avg_val1, avg_val2, avg_val3, karar, st.session_state.user, str(simdi),
            "", "", tat, goruntu, final_not, foto_adi, foto_b64
        ]

        if guvenli_kayit_ekle("Urun_KPI_Kontrol", veri_paketi):
            st.toast("✅ KPI Başarıyla Kaydedildi!"); st.rerun()
        else:
            st.error("❌ Kayıt sırasında veritabanı hatası oluştu.")
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="KPI_KAYDET", tip="UI")

def _render_logo_header():
    try:
        from static.logo_b64 import LOGO_B64
        import base64
        logo_data = LOGO_B64.split(",")[1] if "," in LOGO_B64 else LOGO_B64
        img_bytes = base64.b64decode(logo_data)
        col_logo, col_title = st.columns([1, 5])
        col_logo.image(img_bytes, width=60)
        col_title.markdown("## EKLERİSTAN A.Ş.\n##### KPI & Kalite Kontrol Merkezi")
    except Exception:
        st.markdown("## EKLERİSTAN A.Ş. — Kalite Kontrol")
    st.divider()

def render_kpi_module(engine, guvenli_kayit_ekle):
    """Ana orkestratör — Anayasa Madde 19 Uyumlu."""
    try:
        if not kullanici_yetkisi_var_mi("🍩 KPI & Kalite Kontrol", "Görüntüle"):
            st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır."); st.stop()

        _render_logo_header()
        
        t1, t2 = st.tabs(["📏 Yeni Ölçüm Girişi", "📊 Ölçüm Geçmişi (Raporlama'ya Git)"])
        
        with t1:
            u_df = veri_getir("Ayarlar_Urunler")
            if u_df.empty:
                st.warning("⚠️ Ürün tanımı bulunamadı."); st.stop()

        u_df = bolum_bazli_urun_filtrele(u_df)
        if u_df.empty:
            st.warning("⚠️ Yetkiniz dâhilinde ürün bulunamadı."); st.stop()

        # 1. Ürün Seçimi
        urun_secilen, lot_kpi, vardiya_kpi, urun_ayar = _kpi_urun_sec(u_df)
        if not urun_secilen: return

        # 2. Parametreleri Hazırla
        param_list, numune_adet, raf_omru, stt_date = _kpi_parametre_getir(urun_secilen, urun_ayar)

        # 3. Form Çizimi
        form_data = _kpi_olcum_formu(param_list, numune_adet, stt_date, urun_secilen, raf_omru)

        # 4. Kayıt İşlemi
        if form_data:
            _kpi_kaydet(urun_secilen, lot_kpi, vardiya_kpi, stt_date, numune_adet, param_list, form_data, guvenli_kayit_ekle)
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="KPI_ORCHESTRATOR", tip="UI")
