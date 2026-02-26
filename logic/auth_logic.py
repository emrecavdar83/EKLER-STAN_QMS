import streamlit as st
import pandas as pd
from sqlalchemy import text
from database.connection import get_engine

# Veritabanı motoru (Kullanıcı talimatı: Global engine)
engine = get_engine()

# 1. MODUL_ESLEME dict'i
MODUL_ESLEME = {
    "🏭 Üretim Girişi": "Üretim Girişi",
    "🍩 KPI & Kalite Kontrol": "KPI Kontrol",
    "🛡️ GMP Denetimi": "GMP Denetimi",
    "🧼 Personel Hijyen": "Personel Hijyen",
    "🧹 Temizlik Kontrol": "Temizlik Kontrol",
    "📊 Kurumsal Raporlama": "Raporlama",
    "❄️ Soğuk Oda Sıcaklıkları": "Soğuk Oda",
    "⚙️ Ayarlar": "Ayarlar"
}

@st.cache_data(ttl=60) # Anayasa v2.0 Uyumlu: 60 sn
def kullanici_yetkisi_getir(rol_adi, modul_adi):
    """Belirli rol için modül yetkisini veritabanından çeker"""
    try:
        with engine.connect() as conn:
            sql = text("""
                SELECT erisim_turu FROM ayarlar_yetkiler
                WHERE rol_adi = :rol AND modul_adi = :modul
            """)
            result = conn.execute(sql, {"rol": rol_adi, "modul": modul_adi}).fetchone()
            return result[0] if result else "Yok"
    except:
        return "Yok"

def kullanici_yetkisi_var_mi(menu_adi, gereken_yetki="Görüntüle"):
    """Kullanıcının belirli modüle erişim yetkisini kontrol eder"""
    user_rol = str(st.session_state.get('user_rol', 'PERSONEL')).upper()

    # Admin her şeye erişebilir
    if user_rol in ['ADMIN', 'SİSTEM ADMİN']:
        return True

    # Modül adını veritabanı formatına çevir
    modul_adi = MODUL_ESLEME.get(menu_adi, menu_adi)

    # Yetkiyi kontrol et
    erisim = kullanici_yetkisi_getir(user_rol, modul_adi)

    # Nếu yetki bulunamadıysa (Noktalı İ sorunu), Noktasız I ile tekrar dene
    if erisim == "Yok":
        user_rol_alt = user_rol.replace('İ', 'I')
        erisim = kullanici_yetkisi_getir(user_rol_alt, modul_adi)

    if gereken_yetki == "Görüntüle":
        return erisim.upper() in ["GÖRÜNTÜLE", "DÜZENLE"]
    elif gereken_yetki == "Düzenle":
        return erisim.upper() in ["DÜZENLE"]
    return False

def bolum_bazli_urun_filtrele(urun_df):
    """Bölüm Sorumlusu için ürün listesini hiyerarşik olarak filtreler"""
    user_rol = str(st.session_state.get('user_rol', 'PERSONEL')).upper()
    user_bolum = st.session_state.get('user_bolum', '')
    user_id_str = str(st.session_state.get('user', '')).strip()

    # 1. Admin, Üst Yönetim ve Kalite Ekibi her şeyi görsün
    if user_rol in ['ADMIN', 'YÖNETİM', 'GIDA MÜHENDİSİ'] or \
       'KALİTE' in user_rol or \
       'KALİTE' in str(user_bolum).upper() or \
       'LABORATUVAR' in str(user_bolum).upper() or \
       user_id_str == 'sevcanalbas':
        return urun_df

    # 2. Vardiya Amiri Filtresi
    if (user_rol in ['VARDIYA AMIRI', 'VARDIYA AMİRİ']) and not user_bolum:
        return urun_df

    # 3. Bölüm Sorumlusu Filtresi
    if 'sorumlu_departman' in urun_df.columns and user_bolum:
        try:
            mask_bos = urun_df['sorumlu_departman'].isna() | \
                       (urun_df['sorumlu_departman'] == '') | \
                       (urun_df['sorumlu_departman'].astype(str).str.lower() == 'none')

            mask_eslesme = urun_df['sorumlu_departman'].astype(str).str.contains(str(user_bolum), case=False, na=False)

            return urun_df[mask_bos | mask_eslesme]
        except:
            return urun_df

    # 4. Eski Sistem Uyumluluğu
    elif 'uretim_bolumu' in urun_df.columns and user_bolum:
        return urun_df[urun_df['uretim_bolumu'].astype(str).str.upper() == str(user_bolum).upper()]

    return urun_df
