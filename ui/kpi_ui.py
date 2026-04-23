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

def _kpi_fetch_parameters(urun_secilen, urun_ayar):
    """Parametreleri DB'den veya varsayılanlardan çeker."""
    sql = text("SELECT id, urun_adi, parametre_adi, min_deger, max_deger FROM urun_parametreleri WHERE urun_adi = :u")
    try:
        df = pd.read_sql(sql, engine, params={"u": urun_secilen})
        if not df.empty:
            return df.to_dict('records')
    except Exception:
        pass
    return [{"parametre_adi": urun_ayar.get(f'olcum{i}_ad', f'Ölçüm {i}')} for i in range(1, 4)]

def _kpi_parametre_getir(urun_secilen, urun_ayar):
    """Ürün parametrelerini DB'den çeker ve STT hesaplar."""
    try:
        numune_adet = max(1, int(float(urun_ayar.get('numune_sayisi', 1) or 1)))
        raf_omru = int(float(urun_ayar.get('raf_omru_gun', 0) or 0))
    except Exception:
        numune_adet, raf_omru = 1, 0
    param_list = _kpi_fetch_parameters(urun_secilen, urun_ayar)
    stt_date = get_istanbul_time().date() + timedelta(days=raf_omru)
    return param_list, numune_adet, raf_omru, stt_date

def _kpi_render_pre_checks():
    """STT ve Etiket kontrollerini çizer."""
    st.subheader("✅ Ön Kontroller")
    stt_ok = st.checkbox("Üretim Tarihi ve Son Tüketim Tarihi (STT) Etiket Bilgisi Doğrudur")
    stt_foto = st.file_uploader("📸 STT Etiket Fotoğrafı (Zorunlu)", type=['jpg','png','jpeg'], key="stt_foto_upload")
    st.divider()
    return stt_ok, stt_foto

def _kpi_render_sample_rows(param_list, numune_adet):
    """Numune bazlı ölçüm giriş satırlarını çizer."""
    st.subheader(f"📏 Ölçüm Değerleri ({numune_adet} Numune)")
    all_measurements = []
    for i in range(numune_adet):
        with st.container():
            st.markdown(f"**Numune #{i+1}**")
            cols = st.columns(len(param_list))
            sample_data = {}
            for p_idx, param in enumerate(param_list):
                p_ad, p_min, p_max, p_birim = param.get('parametre_adi',''), param.get('min_deger',0.0), param.get('max_deger',0.0), param.get('birim','')
                if p_ad:
                    u_s = f" {p_birim}" if p_birim else ""
                    b_s = f" [Hedef: {p_min} - {p_max}{u_s}]" if (p_min != 0.0 or p_max != 0.0) else ""
                    val = cols[p_idx % len(cols)].number_input(f"{p_ad}{b_s}", key=f"n{i}_p{p_idx}", step=0.1, min_value=0.0)
                    sample_data[p_ad] = val
            all_measurements.append(sample_data)
            st.markdown("---")
    return all_measurements

def _kpi_render_sensory_checks():
    """Duyusal kontrol alanlarını çizer."""
    st.subheader("Duyusal Kontrol & Sonuç")
    d1, d2 = st.columns(2)
    tat = d1.selectbox("Tat / Koku", ["Uygun", "Uygun Değil"])
    goruntu = d2.selectbox("Görüntü / Renk", ["Uygun", "Uygun Değil"])
    not_kpi = st.text_area("Kalite Notu / Açıklama")
    return tat, goruntu, not_kpi

def _kpi_olcum_formu(param_list, numune_adet, stt_date, urun_secilen, raf_omru):
    """Dinamik ölçüm formunu orkestre eder."""
    st.info(f"ℹ {urun_secilen} Raf Ömrü: {raf_omru} Gün | STT: {stt_date}")
    _v = st.session_state.get('_fv_kpi_form', 0)
    with st.form(f"kpi_form_v{_v}"):
        stt_ok, stt_foto = _kpi_render_pre_checks()
        all_measurements = _kpi_render_sample_rows(param_list, numune_adet)
        tat, goruntu, not_kpi = _kpi_render_sensory_checks()
        if st.form_submit_button("✅ Analizi Kaydet"):
            return {"stt_ok": stt_ok, "stt_foto": stt_foto, "all_measurements": all_measurements,
                    "tat": tat, "goruntu": goruntu, "not_kpi": not_kpi}
    return None

def _kpi_process_photo(stt_foto):
    """Fotografı diske ve base64 formatına hazırlar."""
    os.makedirs("data/uploads/kpi", exist_ok=True)
    f_uzanti = stt_foto.name.split('.')[-1].lower()
    f_adi = f"stt_{get_istanbul_time().strftime('%Y%m%d_%H%M%S')}.{f_uzanti}"
    f_bytes = stt_foto.getbuffer()
    with open(f"data/uploads/kpi/{f_adi}", "wb") as f: f.write(f_bytes)
    import base64 as b64lib
    mime = 'image/jpeg' if f_uzanti in ['jpg', 'jpeg'] else 'image/png'
    f_b64 = f"data:{mime};base64," + b64lib.b64encode(f_bytes).decode('utf-8')
    return f_adi, f_b64

def _kpi_check_and_status(all_measurements, param_list, tat, goruntu):
    """Limit kontrolü yapar ve karar (ONAY/RED) döner."""
    ihlaller = []
    for idx, m in enumerate(all_measurements):
        for p in param_list:
            p_ad, p_min, p_max = p.get('parametre_adi'), float(p.get('min_deger') or 0.0), float(p.get('max_deger') or 0.0)
            val = m.get(p_ad) if p_ad else None
            if val is not None and (p_min != 0.0 or p_max != 0.0) and not (p_min <= float(val) <= p_max):
                ihlaller.append(f"N{idx+1} {p_ad}({val}) hedefi({p_min}-{p_max}) asti")
    karar = "RED" if tat != "Uygun" or goruntu != "Uygun" else ("RED (Deviasyon)" if ihlaller else "ONAY")
    return karar, ihlaller

def _kpi_compile_stats(numune_adet, param_list, all_measurements):
    """Eski Raporlar için ilk 3 parametre ortalamasını hesaplar."""
    avgs = [0.0, 0.0, 0.0]
    for i in range(min(len(param_list), 3)):
        p_name = param_list[i].get('parametre_adi')
        if p_name: avgs[i] = sum([m.get(p_name, 0) for m in all_measurements]) / numune_adet
    return avgs

def _kpi_kaydet(urun_secilen, lot_kpi, vardiya_kpi, stt_date, numune_adet, param_list, form_data, guvenli_kayit_ekle):
    """Kayıt sürecini koordine eder."""
    if not form_data["stt_ok"] or not form_data["stt_foto"]:
        st.error("⛔ STT Doğrulaması ve Fotoğraf Zorunludur!"); return
    try:
        f_adi, f_b64 = _kpi_process_photo(form_data["stt_foto"])
        karar, ihlaller = _kpi_check_and_status(form_data["all_measurements"], param_list, form_data["tat"], form_data["goruntu"])
        avgs = _kpi_compile_stats(numune_adet, param_list, form_data["all_measurements"])
        detay = f"STT OK. " + " ".join([f"[N{i+1}: "+", ".join([f"{k}={v}" for k,v in m.items()])+"]" for i,m in enumerate(form_data["all_measurements"])])
        if ihlaller: detay += " | IHLALLER: " + " ; ".join(ihlaller)
        simdi = get_istanbul_time()
        v_p = [str(simdi.date()), simdi.strftime("%H:%M"), vardiya_kpi, urun_secilen, "", lot_kpi, str(stt_date), str(numune_adet),
               avgs[0], avgs[1], avgs[2], karar, st.session_state.user, str(simdi), "", "", form_data["tat"], form_data["goruntu"],
               f"{form_data['not_kpi']} | {detay}", f_adi, f_b64]
        if guvenli_kayit_ekle("Urun_KPI_Kontrol", v_p):
            _v = st.session_state.get('_fv_kpi_form', 0)
            st.session_state['_fv_kpi_form'] = _v + 1
            st.toast("✅ KPI Kaydedildi!"); st.rerun()
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

def _kpi_load_products():
    """Ürün listesini yetkiye göre yükler."""
    u_df = veri_getir("Ayarlar_Urunler")
    if u_df.empty:
        st.warning("⚠️ Ürün tanımı bulunamadı."); return None
    u_df = bolum_bazli_urun_filtrele(u_df)
    if u_df.empty:
        st.warning("⚠️ Yetkiniz dâhilinde ürün bulunamadı."); return None
    return u_df

def render_kpi_module(engine, guvenli_kayit_ekle):
    """Ana orkestratör (Anayasa Madde 3 Uyumlu)."""
    try:
        if not kullanici_yetkisi_var_mi("🍩 KPI & Kalite Kontrol", "Görüntüle"):
            st.error("🚫 Erişim yetkiniz yok."); st.stop()
        _render_logo_header()
        t1, _ = st.tabs(["📏 Yeni Ölçüm Girişi", "📊 Ölçüm Geçmişi"])
        with t1:
            u_df = _kpi_load_products()
            if u_df is None: return
            res = _kpi_urun_sec(u_df)
            if not res[0]: return
            u_s, l_k, v_k, u_a = res
            p_l, n_a, r_o, s_d = _kpi_parametre_getir(u_s, u_a)
            f_d = _kpi_olcum_formu(p_l, n_a, s_d, u_s, r_o)
            if f_d:
                _kpi_kaydet(u_s, l_k, v_k, s_d, n_a, p_l, f_d, guvenli_kayit_ekle)
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="KPI_ORCHESTRATOR", tip="UI")
