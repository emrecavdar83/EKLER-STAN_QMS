import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import time, pytz

from database.connection import get_engine
from logic.data_fetcher import run_query
from logic.auth_logic import kullanici_yetkisi_var_mi
from logic.cache_manager import CACHE_TTL

engine = get_engine()

def get_istanbul_time():
    now = datetime.now(pytz.timezone('Europe/Istanbul')) \
        if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()
    return now.replace(microsecond=0)

@st.cache_data(ttl=CACHE_TTL['stable'])
def _temizlik_plan_getir():
    """Master planı merkez tanımlarla (Joins) birlikte DB'den çeker."""
    query = """
        SELECT
            p.id, p.kat_id, p.bolum_id, p.ekipman_id,
            l1.ad as kat_ad, l2.ad as bolum_ad, e.ekipman_adi as yer_ekipman,
            p.siklik, p.kimyasal, p.risk, p.metot_id, p.yuzey_tipi,
            p.validasyon_siklik, p.verifikasyon, p.verifikasyon_siklik,
            p.uygulayici, p.kontrol_eden as kontrol_rol,
            p.uygulama_yontemi as metot_detay
        FROM ayarlar_temizlik_plani p
        LEFT JOIN lokasyonlar l1 ON p.kat_id = l1.id
        LEFT JOIN lokasyonlar l2 ON p.bolum_id = l2.id
        LEFT JOIN tanim_ekipmanlar e ON p.ekipman_id = e.id
        WHERE p.durum = 'AKTİF'
    """
    plan_df = pd.read_sql(query, engine)
    return plan_df

def _temizlik_lokasyon_filtrele(plan_df):
    """Kat/Bölüm/Hat selectbox'larını çizer, filtrelenmiş df döndürür."""
    st.caption("📍 **Denetlenecek Lokasyonu Seçin** (Merkez Tanımlar)")
    
    # Kat Listesi (Planda olan katlar)
    katlar_opts = sorted([k for k in plan_df['kat_ad'].unique() if k])
    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
    
    sel_kat = c1.selectbox("🏢 Kat", ["Tümü"] + katlar_opts, key="t_kat_sel")
    
    # Bölüm Listesi
    if sel_kat != "Tümü":
        filtered_bol = plan_df[plan_df['kat_ad'] == sel_kat]
    else:
        filtered_bol = plan_df
        
    bolum_opts = sorted([b for b in filtered_bol['bolum_ad'].unique() if b])
    sel_bolum = c2.selectbox("🏭 Bölüm", ["Tümü"] + bolum_opts, key="t_bol_sel")
    
    # Filtre Uygula
    isler = plan_df.copy()
    f_txt = []
    if sel_kat != "Tümü":
        isler = isler[isler['kat_ad'] == sel_kat]
        f_txt.append(sel_kat)
    if sel_bolum != "Tümü":
        isler = isler[isler['bolum_ad'] == sel_bolum]
        f_txt.append(sel_bolum)

    st.info(f"💡 **{' > '.join(f_txt) if f_txt else 'Tüm Fabrika'}** için **{len(isler)}** görev listelendi.")
    
    vardiya = c4.selectbox("⏰ Vardiya", ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"], key="t_shift")
    
    # ANAYASA v3.0: Hardcoded rol listesi (get_user_roles) kaldırıldı.
    # Modülü görüntüleyen herkes (render_temizlik_module yetkisi varsa) is_controller olabilir,
    # ancak form içeriğini DÜZENLEME yetkisine göre kilitliyoruz.
    is_controller = kullanici_yetkisi_var_mi("🧹 Temizlik Kontrol", "Düzenle")
    
    return isler, vardiya, is_controller

def _temizlik_saha_formu(isler, vardiya, is_controller):
    """Saha uygulama formunu çizer, kayıt listesi döndürür."""
    if not is_controller:
        st.warning(f"⚠️ {st.session_state.user}, bu alanda sadece Görüntüleme yetkiniz var.")
        
    with st.form("temizlik_kayit_formu"):
        kayitlar = []
        h1, h2, h3, h4 = st.columns([3, 2, 2, 2])
        h1.caption("📍 Ekipman / Alan")
        h2.caption("🧪 Kimyasal / Sıklık")
        h3.caption("❓ Durum")
        h4.caption("🔍 Doğrulama / Not")
        st.markdown("---")
        
        for idx, row in isler.iterrows():
            r1, r2, r3, r4 = st.columns([3, 2, 2, 2])
            r1.write(f"**{row['yer_ekipman']}** \n ({row['risk']})")
            r2.caption(f"{row['kimyasal']} \n {row['siklik']}")
            
            with st.expander("ℹ️ Detaylar ve Yöntem"):
                st.markdown(f"**Yöntem:** {row['metot_detay'] if row['metot_detay'] else 'Standart prosedür.'}")
                st.info(f"🧬 **Validasyon:** {row['validasyon_siklik']} | **Verifikasyon:** {row['verifikasyon']} ({row['verifikasyon_siklik']})")
                st.caption(f"**Uygulayıcı:** {row['uygulayici']} | **Kontrol:** {row['kontrol_rol']}")
                
                # --- DİNAMİK VALİDASYON KRİTERLERİ (ADIM 0.1) ---
                if row['metot_id'] and row['yuzey_tipi']:
                    criteria_query = """
                        SELECT min_konsantrasyon, max_konsantrasyon, min_sicaklik, max_sicaklik, temas_suresi_dk, rlu_esik_degeri 
                        FROM temizlik_dogrulama_kriterleri 
                        WHERE metot_id = :m_id AND yuzey_tipi = :y_tipi AND aktif = 1
                    """
                    try:
                        c_df = pd.read_sql(text(criteria_query), engine, params={"m_id": row['metot_id'], "y_tipi": row['yuzey_tipi']})
                        if not c_df.empty:
                            c = c_df.iloc[0]
                            st.markdown("---")
                            st.write("**⚠️ Teknik Limitler:**")
                            col_c1, col_c2 = st.columns(2)
                            if c['min_konsantrasyon'] > 0 or c['max_konsantrasyon'] > 0:
                                col_c1.caption(f"🧪 Dozaj: %{c['min_konsantrasyon']} - %{c['max_konsantrasyon']}")
                            if c['min_sicaklik'] > 0 or c['max_sicaklik'] > 0:
                                col_c1.caption(f"🌡️ Sicaklik: {c['min_sicaklik']}°C - {c['max_sicaklik']}°C")
                            if c['temas_suresi_dk'] > 0:
                                col_c2.caption(f"⏱️ Süre: {c['temas_suresi_dk']} dk")
                            if c['rlu_esik_degeri'] > 0:
                                col_c2.caption(f"✨ RLU Eşiği: < {c['rlu_esik_degeri']}")
                    except: pass

            durum = r3.selectbox("Seç", ["TAMAMLANDI", "YAPILMADI"], key=f"d_{idx}", label_visibility="collapsed", disabled=not is_controller)
            
            val_not = ""
            if durum == "TAMAMLANDI":
                if row['verifikasyon'] and row['verifikasyon'] != 'Görsel':
                    r4.info(f"🧬 {row['verifikasyon']}")
                    val_not = r4.text_input("Sonuç/Not", placeholder="RLU/Puan...", key=f"v_res_{idx}", disabled=not is_controller)
                else:
                    val_not = r4.text_input("Not", key=f"v_note_{idx}", label_visibility="collapsed", disabled=not is_controller)
            else:
                val_not = r4.selectbox("Neden?", ["Arıza", "Malzeme Eksik", "Zaman Yetersiz"], key=f"v_why_{idx}", label_visibility="collapsed", disabled=not is_controller)
            
            if is_controller:
                kayitlar.append({
                    "tarih": str(get_istanbul_time().date()),
                    "saat": get_istanbul_time().strftime("%H:%M"),
                    "kullanici": st.session_state.user,
                    "bolum": row['bolum_ad'], # Eski uyumluluk için metin
                    "lokasyon_id": row['bolum_id'], # Yeni yapı: Bölüm ID
                    "ekipman_id": row['ekipman_id'],
                    "lokasyon_snapshot": f"{row['kat_ad']} > {row['bolum_ad']}",
                    "ekipman_snapshot": row['yer_ekipman'],
                    "islem": row['yer_ekipman'], # Eski uyumluluk
                    "durum": durum,
                    "aciklama": val_not,
                    "vardiya": vardiya
                })
        
        submitted = st.form_submit_button("💾 TÜM KAYITLARI VERİTABANINA İŞLE", width="stretch")
        if submitted:
            return kayitlar
    return None

def _temizlik_kaydet(kayitlar):
    """Kayıtları DB'ye yazar (Atomik İşlem)."""
    if not kayitlar:
        st.warning("İşlenecek kayıt bulunamadı.")
        return

    try:
        # --- ANAYASA v4.0: ATOMIK TRANSACTION ---
        with engine.begin() as conn:
            # İlk kayıttan kolonları al
            cols = ", ".join(kayitlar[0].keys())
            placeholders = ", ".join([f":{k}" for k in kayitlar[0].keys()])
            sql = f"INSERT INTO temizlik_kayitlari ({cols}) VALUES ({placeholders})"
            
            # Batch INSERT (Hız ve Güvenlik için SQLAlchemy native execute)
            conn.execute(text(sql), kayitlar)
            
        st.toast("✅ Tüm kayıtlar başarıyla işlendi!"); st.rerun()
    except Exception as ex:
        from logic.error_handler import handle_exception
        handle_exception(ex, modul="TEMIZLIK_KAYDET", tip="UI")

def render_temizlik_module(engine):
    """Ana orkestratör — Saha uygulama çizelgesini doğrudan render eder."""
    if not kullanici_yetkisi_var_mi("🧹 Temizlik Kontrol", "Görüntüle"):
        st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır."); st.stop()
        
    st.title("🧹 Temizlik ve Sanitasyon Yönetimi")
    
    try:
        plan_df = _temizlik_plan_getir()
        if not plan_df.empty:
            isler, vardiya, is_controller = _temizlik_lokasyon_filtrele(plan_df)
            kayitlar = _temizlik_saha_formu(isler, vardiya, is_controller)
            if kayitlar is not None:
                _temizlik_kaydet(kayitlar)
        else:
            st.warning("⚠️ Master Plan tanımlanmamış. Lütfen Ayarlar modülünden plan oluşturun.")
    except Exception as e:
        from logic.error_handler import handle_exception
        handle_exception(e, modul="TEMIZLIK_ORCHESTRATOR", tip="UI")
