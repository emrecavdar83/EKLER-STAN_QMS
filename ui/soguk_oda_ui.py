# EKLERISTAN QMS - SOSTS Modülü - Tekil UI Katmanı
# V: 2026-03-04-1000-SOZamanRapor

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
    """
    Soğuk Oda Takip Sistemi'nin ana giriş noktası.
    """
    if engine:
        pass # 13. ADAM: Bakım işlemleri (plan_uret, kontrol_geciken_olcumler) app.py'ye (global) taşındı.

    st.title("❄️ Soğuk Oda Takip Sistemi (SOSTS)")
    _render_measurement_tab(engine)


def _render_measurement_tab(engine):
    st.markdown("""<style>.stNumberInput input { font-size: 25px !important; }</style>""", unsafe_allow_html=True)

    token = st.query_params.get("scanned_qr", st.session_state.get("scanned_qr_code", ""))
    user_rol = str(st.session_state.get("user_rol", "Personel")).upper()
    MANUEL_YETKILI_ROLLER = ["ADMIN", "SİSTEM ADMİN", "KALİTE GÜVENCE MÜDÜRÜ"]
    can_manual = user_rol in MANUEL_YETKILI_ROLLER

    # ─── TOKEN YOK → QR EKRANI ──────────────────────────────────────────────
    if not token:
        if can_manual:
            mode = st.radio("Giriş Yöntemi:", ["📸 QR Kodu Tara", "⌨️ Manuel Dolap Seç"], horizontal=True, key="sosts_entry_mode")
            if mode == "⌨️ Manuel Dolap Seç":
                with engine.connect() as conn:
                    rooms_df = pd.read_sql(text("SELECT id, oda_adi, oda_kodu, qr_token FROM soguk_odalar WHERE durum = 'AKTİF'"), conn)
                if not rooms_df.empty:
                    sel_idx = st.selectbox("Dolap Seçiniz:", rooms_df.index, format_func=lambda i: f"{rooms_df.loc[i, 'oda_adi']} ({rooms_df.loc[i, 'oda_kodu']})")
                    if st.button("➡️ Seçili Dolaba Git"):
                        st.session_state.scanned_qr_code = rooms_df.loc[sel_idx, 'qr_token'] or rooms_df.loc[sel_idx, 'oda_kodu']
                        st.rerun()
                else:
                    st.info("Kayıtlı aktif oda bulunamadı.")
                return

        # Telefon kamerası veya bilgisayar kamerası ile doğrudan web uygulamasında okuma
        with st.container(key="scanner_root_container"):
            st.warning("⚠️ Ölçüm kaydı için lütfen dolap üzerindeki QR kodu okutun.", icon="⚠️")
            
            # Kamera Arayüzü
            camera_image = st.camera_input("📸 QR Kodu çekmek için tıklayın veya dokunun (Kameraya İzin Verin)")
            if camera_image:
                try:
                    import cv2
                    import numpy as np

                    bytes_data = camera_image.getvalue()
                    cv2_img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)

                    def _parse_token(raw):
                        return raw.split("scanned_qr=")[-1].strip() if "scanned_qr=" in raw else raw.strip()

                    def _try_detect(img):
                        """Dört kademeli QR algılama: Zxing-cpp → Aruco → klasik → gri+eşikli."""
                        # 0. Zxing-cpp (En güvenilir ve hızlı yöntem, logo dostu)
                        try:
                            import zxingcpp
                            # zxing-cpp usually expects RGB or grayscale. OpenCV uses BGR.
                            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                            results = zxingcpp.read_barcodes(rgb_img)
                            if results:
                                return results[0].text
                        except Exception as e:
                            print(f"Zxing error: {e}")
                            pass
                        
                        # 1. QRCodeDetectorAruco 
                        try:
                            det = cv2.QRCodeDetectorAruco()
                            d, _, _ = det.detectAndDecode(img)
                            if d:
                                return d
                        except Exception:
                            pass
                        # 2. Klasik QRCodeDetector
                        try:
                            det2 = cv2.QRCodeDetector()
                            d2, _, _ = det2.detectAndDecode(img)
                            if d2:
                                return d2
                        except Exception:
                            pass
                        # 3. Gri + adaptif eşik uygulanmış görüntü ile tekrar dene
                        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
                        bgr_thresh = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
                        try:
                            det3 = cv2.QRCodeDetectorAruco()
                            d3, _, _ = det3.detectAndDecode(bgr_thresh)
                            if d3:
                                return d3
                        except Exception:
                            pass
                        return None

                    data = _try_detect(cv2_img)
                    if data:
                        st.session_state.scanned_qr_code = _parse_token(data)
                        st.success("✅ QR Kod algılandı! Yönlendiriliyor...")
                        st.rerun()
                    else:
                        st.error("❌ QR Kodu fotoğrafta tespit edilemedi. Lütfen daha net bir açıdan, kodu ekranın ortasına alarak tekrar çekin.")
                except Exception as e:
                    st.error(f"Kamera okuma sırasında bir hata oluştu: {e}")
            
            st.markdown("---")
            manual_code = st.text_input("⌨️ VEYA Kodu Elle Girin:", placeholder="Örn: auto-gen-3", help="Dolap üzerindeki kodu buraya yazın.")
            if manual_code:
                st.session_state.scanned_qr_code = manual_code.strip()
                st.rerun()
        return

    if not engine:
        return

    # ─── OKUMA: Kısa, izole bağlantı — UI render'dan önce tamamen kapatılır ──
    oda = None
    slot_res = None
    is_pg = engine.dialect.name == 'postgresql'

    try:
        # Poisoned Transaction hatasını engellemek için okuma oturumunu AUTOCOMMIT ile izole et
        read_conn = engine.connect().execution_options(isolation_level="AUTOCOMMIT") if is_pg else engine.connect()
        with read_conn as conn:
            oda = conn.execute(
                text("SELECT id, oda_kodu, oda_adi, departman, min_sicaklik, max_sicaklik, sapma_takip_dakika FROM soguk_odalar WHERE (qr_token = :t OR oda_kodu = :t) AND durum = 'AKTİF'"),
                {"t": token}
            ).fetchone()

            if oda:
                oda_id_tmp = oda[0]
                # Ortak Naive Timezone String'i
                current_time_str = _now().strftime('%Y-%m-%d %H:%M:%S')
                
                if is_pg:
                    # PostgreSQL: Gelecekteki en fazla 15 dakikalık toleransa kadar olan, GEÇMİŞTEKİ en yakın slotu al.
                    # Asla 40 dakika sonraki "başka bir saatin" slotunu kapatmaz! 
                    slot_res = conn.execute(text("""
                        SELECT id, beklenen_zaman, is_takip
                        FROM olcum_plani
                        WHERE oda_id = :oid AND durum IN ('BEKLIYOR', 'GECIKTI')
                        AND beklenen_zaman <= CAST(:now_ts AS TIMESTAMP) + INTERVAL '15 minutes'
                        ORDER BY beklenen_zaman DESC
                        LIMIT 1
                    """), {"oid": oda_id_tmp, "now_ts": current_time_str}).fetchone()
                else:
                    # SQLite: Benzer şekilde 15 dakika tolerans
                    slot_res = conn.execute(text("""
                        SELECT id, beklenen_zaman, is_takip
                        FROM olcum_plani
                        WHERE oda_id = :oid AND durum IN ('BEKLIYOR', 'GECIKTI')
                        AND beklenen_zaman <= datetime(:now_ts, '+15 minutes')
                        ORDER BY beklenen_zaman DESC
                        LIMIT 1
                    """), {"oid": oda_id_tmp, "now_ts": current_time_str}).fetchone()
    except Exception as okuma_hatasi:
        from logic.error_handler import handle_exception
        handle_exception(okuma_hatasi, modul="SOSTS_DB_READ", tip="UI")

    # Oda bulunamadı
    if not oda:
        st.error("❌ Geçersiz QR Kodu! Token: " + str(token))
        if st.button("Sıfırla"):
            st.session_state.scanned_qr_code = ""
            st.rerun()
        return

    oda_id       = oda[0]
    oda_adi      = oda[2]
    oda_kodu     = oda[1]
    oda_min      = oda[4]
    oda_max      = oda[5]
    oda_sapma_dk = oda[6]

    # ─── KULLANICI ARAYÜZÜ ──────────────────────────────────────────────────
    st.success(f"📍 **{oda_adi}** ({oda_kodu})")

    is_takip_gorevi = 0
    if slot_res:
        try:
            slot_saat = slot_res[1].strftime('%H:%M')
        except Exception:
            slot_saat = str(slot_res[1])[:16]
            
        is_takip_gorevi = slot_res[2] if len(slot_res) > 2 else 0
        if is_takip_gorevi:
            st.error("🚨 DİKKAT: BU BİR SAPMA DOĞRULAMA (TAKİP) ÖLÇÜMÜDÜR!")
            st.info(f"🕒 Takip Zaman Dilimi: {slot_saat}")
        else:
            st.info(f"🕒 Eşleşen Zaman Dilimi: {slot_saat}")
    else:
        st.info("ℹ️ Bu oda için şu an planlanmış bir görev yok. Genel ölçüm olarak kaydedilecektir.")

    val = st.number_input("🌡️ Mevcut Sıcaklık (°C)", value=float(oda_min) + 1.0, step=0.1, format="%.1f")
    sapma = val < oda_min or val > oda_max

    if sapma:
        st.error(f"🚨 KRİTİK SAPMA! (Hedef: {oda_min} - {oda_max}°C)")
        aciklama = st.text_area("📝 Sapma Nedeni ve Düzeltici Faaliyet (ZORUNLU):", key="sapma_aciklama")
        takip_dk = int(oda_sapma_dk)
    else:
        st.success("🟢 Sıcaklık Uygun Bölgede.")
        aciklama = ""
        takip_dk = 0

    # ─── KAYDET BUTONU ───────────────────────────────────────────────────────
    if st.button("💾 ÖLÇÜMÜ KAYDET", width="stretch", type="primary"):
        if sapma and not aciklama.strip():
            st.error("⛔ Açıklama zorunludur!")
        else:
            user = st.session_state.get("user", "Saha_Mobil")
            is_scanned = bool(st.query_params.get("scanned_qr"))
            qr_bayrak = 1 if is_scanned else (1 if st.session_state.get("scanned_qr_code") and not can_manual else 0)

            try:
                kaydet_olcum(
                    engine, oda_id, val, user,
                    slot_res[0] if slot_res else None,
                    qr_mi=qr_bayrak,
                    takip_suresi=takip_dk if sapma else None,
                    aciklama=aciklama,
                    is_takip_gorevi=is_takip_gorevi
                )
                st.balloons()
                st.success("✅ Kayıt başarıyla yapıldı!")
                
                # 13. ADAM / ANAYASA MADDE 3: DÖF Hatırlatıcısı
                if sapma:
                    st.warning(f"⚠️ KRİTİK HATIRLATMA: Sapma tespit edildiği için {takip_dk} dakika sonra (DÖF) takip ölçümü yapılması zorunludur. Sistem otomatik takip görevi oluşturmuştur.", icon="🚨")
                    time.sleep(1) # Okuma süresi azaltıldı

                st.session_state.scanned_qr_code = ""
                st.rerun()
            except Exception as kayit_hatasi:
                from logic.error_handler import handle_exception
                handle_exception(kayit_hatasi, modul="SOSTS_SAVE", tip="UI")
