# EKLERISTAN QMS - SOSTS Modülü - Tekil UI Katmanı

import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

from soguk_oda_utils import (
    DB_PATH, qr_uret, qr_toplu_yazdir, plan_uret, 
    kontrol_geciken_olcumler, kaydet_olcum
)

def render_sosts_module(engine=None):
    """
    Soğuk Oda Takip Sistemi'nin ana giriş noktası.
    app.py içerisinden çağrılır.
    """
    # Rutin kontrolleri her yüklemede yap (Lazy Eval)
    plan_uret()
    kontrol_geciken_olcumler()
    
    st.title("❄️ Soğuk Oda Takip Sistemi (SOSTS)")
    
    # URL parametresinden tarama gelmiş mi bak (Operatör kolaylığı için ilk sekme ayarı)
    url_token = st.query_params.get("token", st.session_state.get("scanned_qr_code", ""))
    default_tab = 1 if url_token else 0
    
    tabs = st.tabs(["📊 GÜNLÜK İZLEME", "🌡️ ÖLÇÜM GİRİŞİ", "📈 TREND ANALİZİ", "⚙️ YÖNETİM"])
    
    # -------------------------------------------------------------------------
    # TAB 1: GÜNLÜK İZLEME
    # -------------------------------------------------------------------------
    with tabs[0]:
        _render_monitoring_tab()

    # -------------------------------------------------------------------------
    # TAB 2: ÖLÇÜM GİRİŞİ (Operatör Ekranı)
    # -------------------------------------------------------------------------
    with tabs[1]:
        _render_measurement_tab()

    # -------------------------------------------------------------------------
    # TAB 3: TREND ANALİZİ
    # -------------------------------------------------------------------------
    with tabs[2]:
        _render_analysis_tab()

    # -------------------------------------------------------------------------
    # TAB 4: YÖNETİM (Sadece Yetkililer)
    # -------------------------------------------------------------------------
    with tabs[3]:
        _render_admin_tab()

def _render_monitoring_tab():
    st.subheader("Ölçüm Takip Matrisi")
    sel_date = st.date_input("İzleme Tarihi:", datetime.now(), key="monitor_date")
    
    with sqlite3.connect(DB_PATH) as conn:
        query = """
        SELECT o.oda_adi, p.beklenen_zaman, p.durum, m.sicaklik_degeri
        FROM olcum_plani p
        JOIN soguk_odalar o ON p.oda_id = o.id
        LEFT JOIN sicaklik_olcumleri m ON p.gerceklesen_olcum_id = m.id
        WHERE DATE(p.beklenen_zaman) = ?
        ORDER BY o.oda_adi, p.beklenen_zaman
        """
        df_matris = pd.read_sql(query, conn, params=(str(sel_date),))
    
    if not df_matris.empty:
        df_matris['saat'] = pd.to_datetime(df_matris['beklenen_zaman']).dt.strftime('%H:%M')
        status_icons = {'BEKLIYOR': '⚪', 'TAMAMLANDI': '✅', 'GECIKTI': '⏰', 'ATILDI': '❌'}
        df_matris['display'] = df_matris['durum'].map(status_icons) + " " + df_matris['sicaklik_degeri'].astype(str).replace('nan', '')
        pivot = df_matris.pivot(index='oda_adi', columns='saat', values='display').fillna('—')
        st.table(pivot)
    else:
        st.info("Bu tarih için henüz planlanmış ölçüm bulunmuyor.")

def _render_measurement_tab():
    # CSS: Büyük font
    st.markdown("""<style>.stNumberInput input { font-size: 25px !important; }</style>""", unsafe_allow_html=True)
    
    # Query Params ve Session State entegrasyonu (Stabilizasyon)
    token = st.query_params.get("scanned_qr", st.session_state.get("scanned_qr_code", ""))
    user_rol = str(st.session_state.get("user_rol", "Personel")).upper()
    
    # Anayasa Madde 5 Standartlarına Göre Manuel Giriş Yetkisi Kontrolü
    # Sadece Admin ve Kalite Güvence Müdürü manuel seçim yapabilir
    MANUEL_YETKILI_ROLLER = ["ADMIN", "SİSTEM ADMİN", "KALİTE GÜVENCE MÜDÜRÜ"]
    can_manual = user_rol in MANUEL_YETKILI_ROLLER
    
    if not token:
        with st.container(key="scanner_root_container"):
            st.warning("⚠️ Ölçüm kaydı için lütfen dolap üzerindeki QR kodu okutun.", icon="⚠️")
            
            st.info("💡 Anayasal İzlenebilirlik Kuralı: Sisteme kayıt yapmak için dolabın yanına gidip QR kodu taramanız gerekmektedir. Manuel girişe (yöneticiler dahil) izin verilmemektedir.")
            
            # Streamlit-Native QR Scanner via Camera Input
            img_file = st.camera_input("📸 QR KODU OKUTMAK İÇİN FOTOĞRAF ÇEKİN", key="sosts_camera_input")
            
            if img_file:
                import cv2
                import numpy as np
                
                try:
                    # Byte verisini OpenCV formatına çevir
                    file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
                    opencv_image = cv2.imdecode(file_bytes, 1)
                    
                    # QR Kodunu Çözümle
                    detector = cv2.QRCodeDetector()
                    decoded_text, points, _ = detector.detectAndDecode(opencv_image)
                    
                    if decoded_text:
                        # URL'den token'ı ayıkla veya direkt al
                        scanned_token = ""
                        if "scanned_qr=" in decoded_text:
                            scanned_token = decoded_text.split("scanned_qr=")[1].split("&")[0]
                        else:
                            scanned_token = decoded_text
                        
                        if scanned_token:
                            st.session_state.scanned_qr_code = scanned_token
                            st.toast("✅ Kod başarıyla okundu!", icon="✅")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Geçersiz QR Kod içeriği.")
                    else:
                        st.error("🔍 QR Kod tespit edilemedi. Lütfen kodu net ve yakından fotoğraflayın.")
                except Exception as e:
                    st.error(f"⚠️ Tarama hatası: {e}")
        return

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM soguk_odalar WHERE (qr_token = ? OR oda_kodu = ?) AND aktif = 1", (token, token))
        oda = cursor.fetchone()
        
        if not oda:
            st.error("❌ Geçersiz QR Kodu! Token: " + str(token))
            if st.button("Sıfırla"): st.session_state.scanned_qr_code = ""; st.rerun()
            return

        st.success(f"📍 **{oda['oda_adi']}** ({oda['oda_kodu']})")
        
        # --- AKILLI SLOT EŞLEŞMESİ (Anayasal Madde 3) ---
        # Şu anki saate en yakın 'BEKLIYOR' veya 'GECIKTI' slotunu bulur.
        cursor.execute("""
            SELECT *, ABS(julianday(beklenen_zaman) - julianday('now', 'localtime')) as fark 
            FROM olcum_plani 
            WHERE oda_id = ? AND durum IN ('BEKLIYOR', 'GECIKTI') 
            ORDER BY fark ASC LIMIT 1
        """, (oda['id'],))
        slot = cursor.fetchone()
        
        if slot:
            st.info(f"🕒 Eşleşen Zaman Dilimi: {datetime.fromisoformat(slot['beklenen_zaman']).strftime('%H:%M')}")
        else:
            st.info("ℹ️ Bu oda için şu an planlanmış bir görev yok. Genel ölçüm olarak kaydedilecektir.")
        
        val = st.number_input("🌡️ Mevcut Sıcaklık (°C)", value=oda['min_sicaklik'] + 1.0, step=0.1, format="%.1f")
        
        sapma = val < oda['min_sicaklik'] or val > oda['max_sicaklik']
        if sapma:
            st.error(f"🚨 KRİTİK SAPMA! (Hedef: {oda['min_sicaklik']} - {oda['max_sicaklik']}°C)")
            aciklama = st.text_area("📝 Sapma Nedeni ve Düzeltici Faaliyet (ZORUNLU):", key="sapma_aciklama")
            takip_dk = int(oda.get('sapma_takip_dakika', 30))
            st.warning(f"ℹ️ Admin Talimatı: Sapma sonrası {takip_dk} dakika içinde tekrar kontrol yapılacaktır.")
        else:
            st.success("🟢 Sıcaklık Uygun Bölgede.")
            aciklama = ""
            takip_dk = 0

        if st.button("💾 ÖLÇÜMÜ KAYDET", use_container_width=True, type="primary"):
            if sapma and not aciklama.strip():
                st.error("⛔ Açıklama zorunludur!")
            else:
                user = st.session_state.get("user", "Mobil_User")
                # QR ile mi girildi bayrağı
                # 1. URL'de token/scanned_qr varsa bu fiziksel taramadır.
                # 2. Eğer yetkililer manuel butonla odayı seçtiyse session_state doludur ama URL boştur.
                is_scanned = bool(st.query_params.get("token") or st.query_params.get("scanned_qr"))
                qr_bayrak = 1 if is_scanned else (1 if st.session_state.get("scanned_qr_code") and not can_manual else 0)
                
                res = kaydet_olcum(
                    oda['id'], 
                    val, 
                    user, 
                    slot['id'] if slot else None, 
                    qr_mi=qr_bayrak,
                    takip_suresi=takip_dk if sapma else None
                )
                
                if sapma:
                    st.warning(f"🚨 Sapma nedeniyle {takip_dk} dakika sonrasına otomatik kontrol görevi atandı.")

                st.balloons()
                st.success(f"Kayıt yapıldı. (Yöntem: {'QR Tarama' if qr_bayrak else 'Manuel Giriş'})")
                time.sleep(1)
                st.session_state.scanned_qr_code = ""
                st.rerun()

def _render_analysis_tab():
    st.subheader("Trend ve İstatistikler")
    with sqlite3.connect(DB_PATH) as conn:
        rooms = pd.read_sql("SELECT id, oda_adi FROM soguk_odalar WHERE aktif = 1", conn)
    
    target = st.selectbox("Oda Seçiniz:", rooms['id'], format_func=lambda x: rooms[rooms['id']==x]['oda_adi'].iloc[0])
    
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("""
            SELECT m.olusturulma_tarihi as olcum_zamani, m.sicaklik_degeri, m.sapma_var_mi, o.min_sicaklik, o.max_sicaklik
            FROM sicaklik_olcumleri m JOIN soguk_odalar o ON m.oda_id = o.id
            WHERE m.oda_id = ? ORDER BY m.olusturulma_tarihi ASC
        """, conn, params=(target,))
    
    if not df.empty:
        fig = px.line(df, x='olcum_zamani', y='sicaklik_degeri', title="Sıcaklık Değişim Trendi")
        fig.add_hline(y=df['min_sicaklik'].iloc[0], line_dash="dash", line_color="red")
        fig.add_hline(y=df['max_sicaklik'].iloc[0], line_dash="dash", line_color="red")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Kayıtlı veri bulunamadı.")

def _render_admin_tab():
    user_role = st.session_state.get("user_role", "Admin")
    if user_role not in ["Admin", "Kalite"]:
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
                st.success("Oda eklendi.")
    
    with st.expander("📝 Mevcut Odaları Düzenle"):
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM soguk_odalar WHERE aktif = 1")
            odalar_list = cursor.fetchall()
        
        if odalar_list:
            duzenle_oda = st.selectbox("Düzenlenecek Oda:", odalar_list, format_func=lambda x: f"{x['oda_adi']} ({x['oda_kodu']})")
            if duzenle_oda:
                with st.form(f"edit_form_{duzenle_oda['id']}"):
                    c1, c2 = st.columns(2)
                    new_adi = c1.text_input("Oda Adı:", value=duzenle_oda['oda_adi'])
                    new_kodu = c2.text_input("Oda Kodu:", value=duzenle_oda['oda_kodu'])
                    new_min = c1.number_input("Min Sıcaklık:", value=float(duzenle_oda['min_sicaklik']))
                    new_max = c2.number_input("Max Sıcaklık:", value=float(duzenle_oda['max_sicaklik']))
                    new_takip = c1.number_input("Sapma Takip Süresi (Dk):", value=int(duzenle_oda['sapma_takip_dakika']), min_value=5)
                    new_siklik = c2.number_input("Ölçüm Sıklığı (Saat):", value=int(duzenle_oda.get('olcum_sikligi', 2)), min_value=1)
                    
                    if st.form_submit_button("Değişiklikleri Kaydet"):
                        with sqlite3.connect(DB_PATH) as conn:
                            conn.execute("""
                                UPDATE soguk_odalar 
                                SET oda_adi=?, oda_kodu=?, min_sicaklik=?, max_sicaklik=?, sapma_takip_dakika=?, olcum_sikligi=?
                                WHERE id=?
                            """, (new_adi, new_kodu, new_min, new_max, new_takip, new_siklik, duzenle_oda['id']))
                        st.success("Oda ayarları güncellendi.")
                        time.sleep(1)
                        st.rerun()
        else:
            st.info("Kayıtlı aktif oda bulunamadı.")
                st.rerun()

    st.divider()
    with sqlite3.connect(DB_PATH) as conn:
        odalar = pd.read_sql("SELECT * FROM soguk_odalar", conn)
        st.dataframe(odalar.drop(columns=['qr_token']), use_container_width=True)
        
        sel_rooms = st.multiselect("QR Basılacaklar:", odalar['id'].tolist(), 
                                   format_func=lambda x: odalar[odalar['id']==x]['oda_adi'].iloc[0])
        if sel_rooms and st.button("📦 QR ZIP İNDİR"):
            st.download_button("İndir", data=qr_toplu_yazdir(sel_rooms), file_name="qr.zip")
