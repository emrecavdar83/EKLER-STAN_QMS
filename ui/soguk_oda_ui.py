# EKLERISTAN QMS - SOSTS Modülü - Tekil UI Katmanı

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import text
from datetime import datetime
import time

from soguk_oda_utils import (
    qr_uret, qr_toplu_yazdir, plan_uret,
    kontrol_geciken_olcumler, kaydet_olcum, init_sosts_tables
)

def render_sosts_module(engine=None):
    """
    Soğuk Oda Takip Sistemi'nin ana giriş noktası.
    """
    if engine:
        init_sosts_tables(engine)
        # Rutin kontrolleri her yüklemede yap
        plan_uret(engine)
        kontrol_geciken_olcumler(engine)

    st.title("❄️ Soğuk Oda Takip Sistemi (SOSTS)")

    # URL parametresinden tarama gelmiş mi bak
    url_token = st.query_params.get("scanned_qr", st.session_state.get("scanned_qr_code", ""))
    
    tabs = st.tabs(["📊 GÜNLÜK İZLEME", "🌡️ ÖLÇÜM GİRİŞİ", "📈 TREND ANALİZİ", "⚙️ YÖNETİM"])

    with tabs[0]:
        _render_monitoring_tab(engine)

    with tabs[1]:
        _render_measurement_tab(engine)

    with tabs[2]:
        _render_analysis_tab(engine)

    with tabs[3]:
        _render_admin_tab(engine)

def _render_monitoring_tab(engine):
    st.subheader("Ölçüm Takip Matrisi")
    sel_date = st.date_input("İzleme Tarihi:", datetime.now(), key="monitor_date")

    if not engine:
        st.error("Veritabanı bağlantısı yok.")
        return

    query = """
    SELECT o.oda_adi, p.beklenen_zaman, p.durum, m.sicaklik_degeri
    FROM olcum_plani p
    JOIN soguk_odalar o ON p.oda_id = o.id
    LEFT JOIN sicaklik_olcumleri m ON p.gerceklesen_olcum_id = m.id
    WHERE CAST(p.beklenen_zaman AS DATE) = :d
    ORDER BY o.oda_adi, p.beklenen_zaman
    """
    with engine.connect() as conn:
        df_matris = pd.read_sql(text(query), conn, params={"d": str(sel_date)})

    if not df_matris.empty:
        df_matris['saat'] = pd.to_datetime(df_matris['beklenen_zaman']).dt.strftime('%H:%M')
        status_icons = {'BEKLIYOR': '⚪', 'TAMAMLANDI': '✅', 'GECIKTI': '⏰', 'ATILDI': '❌'}
        df_matris['display'] = df_matris['durum'].map(status_icons) + " " + df_matris['sicaklik_degeri'].astype(str).replace('nan', '')
        pivot = df_matris.pivot(index='oda_adi', columns='saat', values='display').fillna('—')
        st.table(pivot)
    else:
        st.info("Bu tarih için henüz planlanmış ölçüm bulunmuyor.")

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

def _render_analysis_tab(engine):
    st.subheader("Trend ve İstatistikler")
    if not engine: return
    
    with engine.connect() as conn:
        rooms = pd.read_sql(text("SELECT id, oda_adi FROM soguk_odalar WHERE aktif = 1"), conn)

    if rooms.empty:
        st.info("Kayıtlı oda bulunamadı.")
        return

    target = st.selectbox("Oda Seçiniz:", rooms['id'], format_func=lambda x: rooms[rooms['id']==x]['oda_adi'].iloc[0])

    with engine.connect() as conn:
        df = pd.read_sql(text("""
            SELECT m.olusturulma_tarihi as olcum_zamani, m.sicaklik_degeri, m.sapma_var_mi, o.min_sicaklik, o.max_sicaklik
            FROM sicaklik_olcumleri m JOIN soguk_odalar o ON m.oda_id = o.id
            WHERE m.oda_id = :t ORDER BY m.olusturulma_tarihi ASC
        """), conn, params={"t": target})

    if not df.empty:
        fig = px.line(df, x='olcum_zamani', y='sicaklik_degeri', title="Sıcaklık Değişim Trendi")
        fig.add_hline(y=float(df['min_sicaklik'].iloc[0]), line_dash="dash", line_color="red")
        fig.add_hline(y=float(df['max_sicaklik'].iloc[0]), line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Kayıtlı veri bulunamadı.")

def _render_admin_tab(engine):
    user_role = str(st.session_state.get("user_rol", "Personel")).upper()
    if user_role not in ["ADMIN", "SİSTEM ADMİN", "KALİTE GÜVENCE MÜDÜRÜ"]:
        st.warning("Bu sekmeye sadece yöneticiler erişebilir.")
        return

    st.subheader("Sistem Ayarları ve Raporlama")

    with st.expander("🆕 Yeni Oda Ekle"):
        with st.form("admin_oda_ekle"):
            c1, c2 = st.columns(2)
            k = c1.text_input("Kod:")
            a = c2.text_input("Ad:")
            mn = c1.number_input("Min Sıcaklık:", value=0.0)
            mx = c2.number_input("Max Sıcaklık:", value=4.0)
            if st.form_submit_button("Ekle"):
                if k and a:
                    with engine.begin() as conn:
                        conn.execute(text("INSERT INTO soguk_odalar (oda_kodu, oda_adi, min_sicaklik, max_sicaklik) VALUES (:k, :a, :mn, :mx)"),
                                     {"k": k, "a": a, "mn": mn, "mx": mx})
                    st.success("Oda eklendi.")
                    st.rerun()

    with st.expander("📝 Mevcut Odaları Düzenle"):
        with engine.connect() as conn:
            odalar_list = conn.execute(text("SELECT * FROM soguk_odalar WHERE aktif = 1")).fetchall()

        if odalar_list:
            duzenle_oda = st.selectbox("Düzenlenecek Oda:", odalar_list, format_func=lambda x: f"{x[2]} ({x[1]})") # x[2]: oda_adi, x[1]: oda_kodu
            if duzenle_oda:
                with st.form(f"edit_form_{duzenle_oda[0]}"):
                    c1, c2 = st.columns(2)
                    new_adi = c1.text_input("Oda Adı:", value=duzenle_oda[2])
                    new_kodu = c2.text_input("Oda Kodu:", value=duzenle_oda[1])
                    new_min = c1.number_input("Min Sıcaklık:", value=float(duzenle_oda[4]))
                    new_max = c2.number_input("Max Sıcaklık:", value=float(duzenle_oda[5]))
                    new_takip = c1.number_input("Sapma Takip Süresi (Dk):", value=int(duzenle_oda[6]), min_value=5)
                    new_siklik = c2.number_input("Ölçüm Sıklığı (Saat):", value=int(odalar_list[0][7]) if len(odalar_list[0])>7 else 2, min_value=1)

                    if st.form_submit_button("Değişiklikleri Kaydet"):
                        with engine.begin() as conn:
                            conn.execute(text("""
                                UPDATE soguk_odalar
                                SET oda_adi=:a, oda_kodu=:k, min_sicaklik=:mn, max_sicaklik=:mx, sapma_takip_dakika=:t, olcum_sikligi=:s
                                WHERE id=:id
                            """), {"a": new_adi, "k": new_kodu, "mn": new_min, "mx": new_max, "t": new_takip, "s": new_siklik, "id": duzenle_oda[0]})
                        st.success("Oda ayarları güncellendi.")
                        time.sleep(1)
                        st.rerun()
        else:
            st.info("Kayıtlı aktif oda bulunamadı.")

    st.divider()
    if engine:
        with engine.connect() as conn:
            odalar = pd.read_sql(text("SELECT * FROM soguk_odalar"), conn)
            st.dataframe(odalar.drop(columns=['qr_token']), use_container_width=True)

            sel_rooms = st.multiselect("QR Basılacaklar:", odalar['id'].tolist(),
                                       format_func=lambda x: odalar[odalar['id']==x]['oda_adi'].iloc[0])
            if sel_rooms and st.button("📦 QR ZIP İNDİR"):
                st.download_button("İndir", data=qr_toplu_yazdir(engine, sel_rooms), file_name="qr.zip")
