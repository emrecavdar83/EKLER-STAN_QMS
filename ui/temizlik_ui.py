import streamlit as st
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import time, pytz

from database.connection import get_engine
from logic.data_fetcher import run_query, get_user_roles

engine = get_engine()

def get_istanbul_time():
    return datetime.now(pytz.timezone('Europe/Istanbul')) \
        if 'Europe/Istanbul' in pytz.all_timezones else datetime.now()

def _temizlik_plan_getir():
    """Master planı DB'den çeker, hiyerarşi sütunlarını ayrıştırır."""
    query = """
        SELECT
            rowid as id,
            COALESCE(kat, '') as kat_adi,
            kat_bolum as kat_bolum_full,
            yer_ekipman as ekipman_alan,
            siklik,
            kimyasal as kimyasal_adi,
            risk as risk_seviyesi,
            validasyon_siklik,
            verifikasyon,
            verifikasyon_siklik,
            uygulayici,
            kontrol_eden as kontrol_rol,
            uygulama_yontemi as metot_detay,
            metot_id,
            yuzey_tipi
        FROM ayarlar_temizlik_plani
    """
    plan_df = pd.read_sql(query, engine)
    
    if not plan_df.empty:
        def parse_hierarchy(row):
            full = row['kat_bolum_full'] or ""
            parts = [p.strip() for p in full.split(">")]
            kat = row['kat_adi'] if row['kat_adi'] else (parts[0] if len(parts) > 0 else "")
            bolum = parts[1] if len(parts) > 1 else (parts[0] if len(parts) == 1 else "")
            hat = parts[2] if len(parts) > 2 else ""
            return pd.Series([kat, bolum, hat])

        plan_df[['kat_parsed', 'bolum_parsed', 'hat_parsed']] = plan_df.apply(parse_hierarchy, axis=1)
    
    return plan_df

def _temizlik_lokasyon_filtrele(plan_df):
    """Kat/Bölüm/Hat/Vardiya selectbox'larını çizer, filtrelenmiş df döndürür."""
    katlar_unique = sorted([k for k in plan_df['kat_parsed'].unique() if k])
    
    st.caption("📍 **Denetlenecek Lokasyonu Seçin** (Hiyerarşik Filtreleme)")
    c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
    
    sel_kat = c1.selectbox("🏢 Kat", ["Tümü"] + katlar_unique, key="saha_kat_select")
    
    if sel_kat != "Tümü":
        bolumler_unique = sorted([b for b in plan_df[plan_df['kat_parsed'] == sel_kat]['bolum_parsed'].unique() if b])
    else:
        bolumler_unique = sorted([b for b in plan_df['bolum_parsed'].unique() if b])
    
    sel_bolum = c2.selectbox("🏭 Bölüm", ["Tümü"] + bolumler_unique, key="saha_bolum_select")
    
    filtered_for_hat = plan_df.copy()
    if sel_kat != "Tümü": filtered_for_hat = filtered_for_hat[filtered_for_hat['kat_parsed'] == sel_kat]
    if sel_bolum != "Tümü": filtered_for_hat = filtered_for_hat[filtered_for_hat['bolum_parsed'] == sel_bolum]
    
    hatlar_unique = sorted([h for h in filtered_for_hat['hat_parsed'].unique() if h])
    if hatlar_unique:
        sel_hat = c3.selectbox("🛤️ Hat", ["Tümü"] + hatlar_unique, key="saha_hat_select")
    else:
        sel_hat = "Tümü"
        c3.selectbox("🛤️ Hat", ["Hat Yok"], disabled=True, key="saha_hat_disabled")
        
    vardiya = c4.selectbox("⏰ Vardiya", ["GÜNDÜZ VARDİYASI", "ARA VARDİYA", "GECE VARDİYASI"], key="t_v_apply")
    
    isler = plan_df.copy()
    filter_desc = []
    if sel_kat != "Tümü":
        isler = isler[isler['kat_parsed'] == sel_kat]
        filter_desc.append(f"🏢 {sel_kat}")
    if sel_bolum != "Tümü":
        isler = isler[isler['bolum_parsed'] == sel_bolum]
        filter_desc.append(f"🏭 {sel_bolum}")
    if sel_hat != "Tümü" and hatlar_unique:
        isler = isler[isler['hat_parsed'] == sel_hat]
        filter_desc.append(f"🛤️ {sel_hat}")
        
    filter_text = " > ".join(filter_desc) if filter_desc else "🌐 Tüm Lokasyonlar"
    st.info(f"💡 **{filter_text}** için **{len(isler)}** adet temizlik görevi listelendi.")
    
    ADMIN_USERS, CONTROLLER_ROLES = get_user_roles()
    is_controller = (st.session_state.user in CONTROLLER_ROLES) or (st.session_state.user in ADMIN_USERS)
    
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
            r1.write(f"**{row['ekipman_alan']}** \n ({row['risk_seviyesi']})")
            r2.caption(f"{row['kimyasal_adi']} \n {row['siklik']}")
            
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
                    "bolum": row['bolum_parsed'],
                    "islem": row['ekipman_alan'],
                    "durum": durum,
                    "aciklama": val_not
                })
        
        submitted = st.form_submit_button("💾 TÜM KAYITLARI VERİTABANINA İŞLE", use_container_width=True)
        if submitted:
            return kayitlar
    return None

def _temizlik_kaydet(kayitlar):
    """Kayıtları DB'ye yazar."""
    if kayitlar:
        try:
            pd.DataFrame(kayitlar).to_sql("temizlik_kayitlari", engine, if_exists='append', index=False)
            st.success("✅ Kayıtlar başarıyla işlendi!"); time.sleep(1); st.rerun()
        except Exception as ex:
            st.error(f"Veritabanına yazılırken hata: {ex}")
    else:
        st.warning("İşlenecek kayıt bulunamadı.")

def _temizlik_master_goster():
    """Master plan görüntüleme tabını çizer (read-only)."""
    st.subheader("⚙️ Master Temizlik Planı (Görüntüleme)")
    st.info("💡 Bu ekranda Ayarlar modülünde oluşturulan Master Temizlik Planını görüntüleyebilirsiniz. Değişiklik yapmak için **⚙️ Ayarlar > Temizlik Yönetimi** sayfasını kullanın.")
    
    try:
        master_df = pd.read_sql("SELECT * FROM ayarlar_temizlik_plani", engine)
        if not master_df.empty:
            if 'id' not in master_df.columns:
                master_df.insert(0, 'id', range(1, len(master_df) + 1))
            
            display_columns = {
                'id': 'Plan ID', 'kat': '🏢 Kat', 'kat_bolum': '🏭 Bölüm', 'yer_ekipman': '⚙️ Ekipman/Alan',
                'kimyasal': '🧪 Kimyasal', 'uygulama_yontemi': '📋 Yöntem', 'uygulayici': '👷 Uygulayıcı',
                'kontrol_eden': '👤 Kontrol', 'siklik': '🔄 Sıklık', 'validasyon_siklik': '✅ Validasyon',
                'verifikasyon': '🔬 Verifikasyon Yöntemi', 'verifikasyon_siklik': '📅 Verif. Sıklığı', 'risk': '⚠️ Risk'
            }
            existing_cols = [col for col in display_columns.keys() if col in master_df.columns]
            display_df = master_df[existing_cols].rename(columns={k: v for k, v in display_columns.items() if k in existing_cols})
            
            st.dataframe(display_df, use_container_width=True, hide_index=True, height=600)
            st.success(f"✅ {len(master_df)} adet temizlik planı kaydı görüntüleniyor.")
        else:
            st.warning("⚠️ Henüz Master Temizlik Planı tanımlanmamış.")
    except Exception as e:
        st.error(f"Master plan yüklenirken hata oluştu: {e}")

def render_temizlik_module(engine):
    """Ana orkestratör — iki tabı yönetir."""
    if not kullanici_yetkisi_var_mi("🧹 Temizlik Kontrol", "Görüntüle"):
        st.error("🚫 Bu modüle erişim yetkiniz bulunmamaktadır."); st.stop()
        
    st.title("🧹 Temizlik ve Sanitasyon Yönetimi")
    tab_uygulama, tab_master_plan = st.tabs(["📋 Saha Uygulama Çizelgesi", "⚙️ Master Plan Düzenleme"])
    
    with tab_uygulama:
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
            st.error(f"Saha formu yüklenirken hata oluştu: {e}")
            
    with tab_master_plan:
        _temizlik_master_goster()
