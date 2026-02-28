# EKLERISTAN QMS - SOSTS Modülü - Tekil UI Katmanı

import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import time

from soguk_oda_utils import (
    plan_uret, kontrol_geciken_olcumler, 
    kaydet_olcum, init_sosts_tables
)

def render_sosts_module(engine=None):
    """
    Soğuk Oda Takip Sistemi'nin ana giriş noktası.
    """
    if engine:
        # PERFORMANS: Rutin kontrolleri (Tablo init, Plan) her saniye değil, 1 saatte bir yap
        current_time = time.time()
        last_check = st.session_state.get("sosts_last_maintenance", 0)
        
        # SIFIR HARDCODE (Madde 1): Periyodu DB'den çek
        bakim_periyodu = 3600  # Varsayılan
        try:
            with engine.connect() as conn:
                res_p = conn.execute(text("SELECT deger FROM sistem_parametreleri WHERE anahtar = 'sosts_bakim_periyodu_sn'")).fetchone()
                if res_p:
                    bakim_periyodu = int(res_p[0])
        except Exception:
            # Tablo henüz yoksa (Örn: İlk kurulum), bakımı zorla tetikle (periyot = 0)
            bakim_periyodu = 0
        
        if (current_time - last_check) > bakim_periyodu: 
            init_sosts_tables(engine)
            plan_uret(engine)
            kontrol_geciken_olcumler(engine)
            st.session_state.sosts_last_maintenance = current_time

    st.title("❄️ Soğuk Oda Takip Sistemi (SOSTS)")

    # URL parametresinden tarama gelmiş mi bak
    url_token = st.query_params.get("scanned_qr", st.session_state.get("scanned_qr_code", ""))
    
    _render_measurement_tab(engine)


def _render_measurement_tab(engine):
    st.markdown("""<style>.stNumberInput input { font-size: 25px !important; }</style>""", unsafe_allow_html=True)

    token = st.query_params.get("scanned_qr", st.session_state.get("scanned_qr_code", ""))
    user_rol = str(st.session_state.get("user_rol", "Personel")).upper()
    MANUEL_YETKILI_ROLLER = ["ADMIN", "SİSTEM ADMİN", "KALİTE GÜVENCE MÜDÜRÜ"]
    can_manual = user_rol in MANUEL_YETKILI_ROLLER

    if not token:
        # Yetkili kullanıcılar için manuel seçim opsiyonu
        if can_manual:
            mode = st.radio("Giriş Yöntemi:", ["📸 QR Kodu Tara", "⌨️ Manuel Dolap Seç"], horizontal=True, key="sosts_entry_mode")
            if mode == "⌨️ Manuel Dolap Seç":
                with engine.connect() as conn:
                    rooms_df = pd.read_sql(text("SELECT id, oda_adi, oda_kodu, qr_token FROM soguk_odalar WHERE aktif = 1"), conn)
                if not rooms_df.empty:
                    sel_idx = st.selectbox("Dolap Seçiniz:", rooms_df.index, format_func=lambda i: f"{rooms_df.loc[i, 'oda_adi']} ({rooms_df.loc[i, 'oda_kodu']})")
                    if st.button("➡️ Seçili Dolaba Git"):
                        st.session_state.scanned_qr_code = rooms_df.loc[sel_idx, 'qr_token'] or rooms_df.loc[sel_idx, 'oda_kodu']
                        st.rerun()
                else:
                    st.info("Kayıtlı aktif oda bulunamadı.")
                return

        # Kamera kontrolü
        show_cam = st.session_state.get("show_sosts_camera", False)
        
        if show_cam:
            if st.button("❌ Taramayı İptal Et", use_container_width=True):
                st.session_state.show_sosts_camera = False
                st.rerun()

            img_file = st.camera_input("📸 QR KODU OKUTMAK İÇİN FOTOĞRAF ÇEKİN", key="sosts_camera_input")

            if img_file:
                import cv2
                import numpy as np
                try:
                    file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
                    opencv_image = cv2.imdecode(file_bytes, 1)
                    detector = cv2.QRCodeDetector()
                    decoded_text, points, _ = detector.detectAndDecode(opencv_image)
                    if decoded_text:
                        scanned_token = decoded_text.split("scanned_qr=")[1].split("&")[0] if "scanned_qr=" in decoded_text else decoded_text
                        if scanned_token:
                            st.session_state.scanned_qr_code = scanned_token
                            st.session_state.show_sosts_camera = False # Başarılı tarama sonrası kamerayı kapat
                            st.toast("✅ Kod başarıyla okundu!", icon="✅")
                            time.sleep(0.5)
                            st.rerun()
                    else:
                        st.error("🔍 QR Kod tespit edilemedi. Lütfen daha net bir fotoğraf çekin.")
                except Exception as e:
                    st.error(f"⚠️ Tarama hatası: {e}")
        else:
            with st.container(key="scanner_root_container"):
                st.warning("⚠️ Ölçüm kaydı için lütfen dolap üzerindeki QR kodu okutun.", icon="⚠️")
                st.info("💡 Anayasal İzlenebilirlik Kuralı: Sisteme kayıt yapmak için dolabın yanına gidip QR kodu taramanız gerekmektedir.")
                if st.button("📸 Taramayı Başlat", use_container_width=True, type="primary"):
                    st.session_state.show_sosts_camera = True
                    st.rerun()
        return

    if not engine: return

    with engine.connect() as conn:
        oda = conn.execute(text("SELECT * FROM soguk_odalar WHERE (qr_token = :t OR oda_kodu = :t) AND aktif = 1"), {"t": token}).fetchone()

        if not oda:
            st.error("❌ Geçersiz QR Kodu! Token: " + str(token))
            if st.button("Sıfırla"): st.session_state.scanned_qr_code = ""; st.rerun()
            return

        # oda bir Row objesi, index veya key ile erişilmelidir.
        oda_id = oda[0] # "id" sütunu genelde ilk sütundur
        oda_adi = oda[2]
        oda_kodu = oda[1]
        oda_min = oda[4]
        oda_max = oda[5]
        oda_sapma_dk = oda[6]

        st.success(f"📍 **{oda_adi}** ({oda_kodu})")

        slot_res = conn.execute(text("""
            SELECT id, beklenen_zaman
            FROM olcum_plani
            WHERE oda_id = :oid AND durum IN ('BEKLIYOR', 'GECIKTI')
            ORDER BY ABS(EXTRACT(EPOCH FROM (beklenen_zaman - CURRENT_TIMESTAMP))) ASC LIMIT 1
        """), {"oid": oda_id}).fetchone()

        if slot_res:
             st.info(f"🕒 Eşleşen Zaman Dilimi: {slot_res[1].strftime('%H:%M')}")
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

        if st.button("💾 ÖLÇÜMÜ KAYDET", use_container_width=True, type="primary"):
            if sapma and not aciklama.strip():
                st.error("⛔ Açıklama zorunludur!")
            else:
                user = st.session_state.get("user", "Mobil_User")
                is_scanned = bool(st.query_params.get("scanned_qr"))
                qr_bayrak = 1 if is_scanned else (1 if st.session_state.get("scanned_qr_code") and not can_manual else 0)

                kaydet_olcum(engine, oda_id, val, user, slot_res[0] if slot_res else None, qr_mi=qr_bayrak, takip_suresi=takip_dk if sapma else None)
                st.balloons()
                st.success(f"Kayıt yapıldı.")
                time.sleep(1)
                st.session_state.scanned_qr_code = ""
                st.rerun()

