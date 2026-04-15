# EKLERISTAN QMS - SOSTS Modülü - Tekil UI Katmanı
# V: 2026-04-15-Refactor-30Line

import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import time

from soguk_oda_utils import (
    plan_uret, kontrol_geciken_olcumler, 
    kaydet_olcum, init_sosts_tables, _now, get_sosts_param
)

def render_sosts_module(engine=None):
    """Soğuk Oda Takip Sistemi'nin ana giriş noktası."""
    st.title("❄️ Soğuk Oda Takip Sistemi (SOSTS)")
    _render_measurement_tab(engine)

def _sosts_qr_detect(img):
    """Dört kademeli QR algılama (Zxing-cpp → Aruco → klasik → gri+eşikli)."""
    import cv2
    import numpy as np
    try:
        import zxingcpp
        r = zxingcpp.read_barcodes(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if r: return r[0].text
    except Exception: pass
    
    for det in [cv2.QRCodeDetectorAruco(), cv2.QRCodeDetector()]:
        try:
            d, _, _ = det.detectAndDecode(img)
            if d: return d
        except Exception: pass
    
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        d3, _, _ = cv2.QRCodeDetectorAruco().detectAndDecode(cv2.cvtColor(thr, cv2.COLOR_GRAY2BGR))
        if d3: return d3
    except Exception: pass
    return None

def _sosts_render_qr_scanner():
    """Kamera arayüzü ve QR algılama."""
    with st.container(key="scanner_container"):
        st.warning("⚠️ Ölçüm kaydı için lütfen dolap üzerindeki QR kodu okutun.")
        cam = st.camera_input("📸 QR Kodu çekin")
        if cam:
            try:
                import cv2
                import numpy as np
                img = cv2.imdecode(np.frombuffer(cam.getvalue(), np.uint8), cv2.IMREAD_COLOR)
                data = _sosts_qr_detect(img)
                if data:
                    token = data.split("scanned_qr=")[-1].strip() if "scanned_qr=" in data else data.strip()
                    st.session_state.scanned_qr_code = token
                    st.success("✅ QR Kod algılandı!"); st.rerun()
                else: st.error("❌ QR Kodu tespit edilemedi. Lütfen tekrar çekin.")
            except Exception as e: st.error(f"Kamera hatası: {e}")
        st.markdown("---")
        code = st.text_input("⌨️ VEYA Kodu Elle Girin:", placeholder="Örn: auto-gen-3")
        if code: st.session_state.scanned_qr_code = code.strip(); st.rerun()

def _sosts_render_manual_selection(engine):
    """Yetkili kullanıcılar için manuel oda seçimi."""
    st.info("💡 Yetkili: Manuel oda seçebilirsiniz.")
    with engine.connect() as conn:
        df = pd.read_sql(text("SELECT id, oda_adi, oda_kodu, qr_token FROM soguk_odalar WHERE durum = 'AKTİF'"), conn)
    if not df.empty:
        sel = st.selectbox("Dolap Seç:", df.index, format_func=lambda i: f"{df.loc[i, 'oda_adi']} ({df.loc[i, 'oda_kodu']})")
        if st.button("➡️ Git"):
            st.session_state.scanned_qr_code = df.loc[sel, 'qr_token'] or df.loc[sel, 'oda_kodu']
            st.rerun()
    else: st.info("Aktif oda yok.")

def _sosts_fetch_oda_and_slot(engine, token):
    """Seçili oda ve uygun ölçüm slotunu çeker."""
    is_pg = engine.dialect.name == 'postgresql'
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
            oda = conn.execute(text("SELECT id, oda_kodu, oda_adi, min_sicaklik, max_sicaklik, sapma_takip_dakika FROM soguk_odalar WHERE (qr_token = :t OR oda_kodu = :t) AND durum = 'AKTİF'"), {"t": token}).fetchone()
            if not oda: return None, None
            now_str = _now().strftime('%Y-%m-%d %H:%M:%S')
            sql = f"""SELECT id, beklenen_zaman, is_takip FROM olcum_plani WHERE oda_id=:oid AND durum IN ('BEKLIYOR', 'GECIKTI') 
                    AND beklenen_zaman <= {'CAST(:now AS TIMESTAMP) + INTERVAL \'15 minutes\'' if is_pg else 'datetime(:now, \'+15 minutes\')'} 
                    ORDER BY beklenen_zaman DESC LIMIT 1"""
            slot = conn.execute(text(sql), {"oid": oda[0], "now": now_str}).fetchone()
            return oda, slot
    except Exception: return None, None

def _sosts_handle_save(engine, oda, slot, val, sapma, aciklama):
    """Kayıt işlemini gerçekleştirir."""
    if sapma and not aciklama.strip():
        st.error("⛔ Açıklama zorunludur!"); return
    
    try:
        user = st.session_state.get("user", "Saha_Mobil")
        qr_mi = 1 if st.query_params.get("scanned_qr") or (st.session_state.get("scanned_qr_code") and st.session_state.get("user_rol") not in ["ADMIN"]) else 0
        kaydet_olcum(engine, oda[0], val, user, slot[0] if slot else None, qr_mi=qr_mi, takip_suresi=int(oda[5]) if sapma else None, aciklama=aciklama, is_takip_gorevi=slot[2] if slot else 0)
        st.balloons(); st.success("✅ Kayıt başarılı!")
        if sapma: st.warning(f"🚨 {oda[5]} dakika sonra takip ölçümü zorunludur!")
        st.session_state.scanned_qr_code = ""; time.sleep(0.5); st.rerun()
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="SOSTS_SAVE", tip="UI")

def _sosts_render_measurement_form(engine, oda, slot):
    """Ölçüm giriş formu."""
    st.success(f"📍 **{oda[2]}** ({oda[1]})")
    if slot:
        st.info(f"🕒 {'🚨 TAKİP ÖLÇÜMÜ: ' if slot[2] else 'Eşleşen: '}{slot[1].strftime('%H:%M') if hasattr(slot[1], 'strftime') else str(slot[1])[:16]}")
    else: st.info("ℹ️ Genel ölçüm olarak kaydedilecektir.")
    
    val = st.number_input("🌡️ Sıcaklık (°C)", value=float(oda[3]) + 1.0, step=0.1, format="%.1f")
    sapma = val < oda[3] or val > oda[4]
    
    if sapma:
        st.error(f"🚨 KRİTİK SAPMA! ({oda[3]} - {oda[4]}°C)")
        aciklama = st.text_area("📝 Neden ve DÖF (ZORUNLU):", key="sapma_aciklama")
    else: st.success("🟢 Uygun."); aciklama = ""
    
    if st.button("💾 KAYDET", width="stretch", type="primary"):
        _sosts_handle_save(engine, oda, slot, val, sapma, aciklama)

def _render_measurement_tab(engine):
    """SOSTS Ölçüm Sekmesi Orkestratörü."""
    st.markdown("<style>.stNumberInput input { font-size: 25px !important; }</style>", unsafe_allow_html=True)
    token = st.query_params.get("scanned_qr", st.session_state.get("scanned_qr_code", ""))
    can_manual = str(st.session_state.get("user_rol", "Personel")).upper() in ["ADMIN", "SİSTEM ADMİN", "KALİTE GÜVENCE MÜDÜRÜ"]

    if not token:
        if can_manual and st.radio("Yöntem:", ["📸 QR Tara", "⌨️ Manuel Seç"], horizontal=True) == "⌨️ Manuel Seç":
             _sosts_render_manual_selection(engine)
        else: _sosts_render_qr_scanner()
        return

    oda, slot = _sosts_fetch_oda_and_slot(engine, token)
    if not oda:
        st.error(f"❌ Geçersiz QR! ({token})")
        if st.button("Sıfırla"): st.session_state.scanned_qr_code = ""; st.rerun()
        return

    _sosts_render_measurement_form(engine, oda, slot)
