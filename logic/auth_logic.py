import streamlit as st
import pandas as pd
from sqlalchemy import text
from database.connection import get_engine

# Veritabanı motoru (Kullanıcı talimatı: Global engine)
engine = get_engine()

print(f"DEBUG: auth_logic.py loaded from {__file__}")
import os
print(f"DEBUG: FORCE_DINAMIK_USER env: {os.environ.get('FORCE_DINAMIK_USER')}")

# 1. MODUL_ESLEME dict'i (Eski Sistem Bağlantısı)
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

# --- SIFIR HARDCODE: YARDIMCI VE GÖLGE KATMAN (ZERO-DOWNTIME SCAFFOLD) ---

def _normalize_string(s):
    """Türkçe ve özel karakterleri (emoji dahil) temizleyen ASCII normalizasyon."""
    if not s: return ""
    # Sadece harf ve rakamları tut, büyük harfe çevir
    s = str(s).upper()
    import re
    # Türkçe karakterleri elle çevir
    translation = str.maketrans("İÜÖÇŞĞ", "IUOCSG")
    s = s.translate(translation)
    # Geri kalan alfa-numerik olmayan her şeyi temizle (Emojiler dahil)
    s = "".join(re.findall(r'[A-Z0-9\s]', s))
    return s.strip()

def _dinamik_yetki_aktif_mi():
    """Anayasa v2.0: Sadece test kullanıcısı için yeni mimariyi açar.
    CLI ortamında testler için ENV (FORCE_DINAMIK_USER) desteği eklenmiştir.
    """
    import os
    env_user = os.environ.get('FORCE_DINAMIK_USER', '').strip().lower()
    if env_user == "test_kullanici": return True
    
    user = str(st.session_state.get('user', '')).strip().lower()
    return user == "test_kullanici"

@st.cache_data(ttl=60)
def _get_dinamik_modul_anahtari(menu_adi):
    """Menü etiketinden veritabanı anahtarını (modul_anahtari) bulur.
    Emojilerden ve Windows case-insensitive sorunlarından etkilenmemek için normalize edilmiş arama yapar.
    """
    try:
        with engine.connect() as conn:
            # Önce tam eşleşme
            sql = text("SELECT modul_anahtari FROM ayarlar_moduller WHERE modul_etiketi = :m OR modul_anahtari = :m")
            res = conn.execute(sql, {"m": menu_adi}).fetchone()
            if res: return res[0]
            
            # Emojisiz ve normalize edilmiş eşleşme için tüm modülleri çek
            all_mods = conn.execute(text("SELECT modul_anahtari, modul_etiketi FROM ayarlar_moduller")).fetchall()
            
            clean_menu = _normalize_string(menu_adi)
            # Eğer menü adında emoji varsa temizlemeye çalışalım (Basit yöntem: sadece harf ve rakamları tut)
            clean_menu_only_alnum = "".join(c for c in clean_menu if c.isalnum() or c.isspace())

            for anahtar, etiket in all_mods:
                target_anahtar_norm = _normalize_string(anahtar)
                target_etiket_norm = _normalize_string(etiket)
                
                # DEBUG: Sadece test kullanıcısı için bas
                if _dinamik_yetki_aktif_mi():
                    print(f"DEBUG: Comparing '{clean_menu}' with Label:'{target_etiket_norm}' Key:'{target_anahtar_norm}'")

                # Kademeli kontrol
                if clean_menu in target_etiket_norm or target_etiket_norm in clean_menu:
                    if _dinamik_yetki_aktif_mi(): print(f"DEBUG: MATCH FOUND (Type 1): {anahtar}")
                    return anahtar
                if clean_menu_only_alnum and (clean_menu_only_alnum in target_etiket_norm or target_etiket_norm in clean_menu_only_alnum):
                    if _dinamik_yetki_aktif_mi(): print(f"DEBUG: MATCH FOUND (Type 2): {anahtar}")
                    return anahtar
                if clean_menu == target_anahtar_norm or clean_menu_only_alnum == target_anahtar_norm:
                    if _dinamik_yetki_aktif_mi(): print(f"DEBUG: MATCH FOUND (Type 3): {anahtar}")
                    return anahtar
            
            if _dinamik_yetki_aktif_mi(): print(f"DEBUG: NO MATCH FOR {menu_adi}")
            return menu_adi
    except:
        return menu_adi

@st.cache_data(ttl=60)
def kullanici_yetkisi_getir_dinamik(rol_adi, modul_anahtar):
    """Anayasa v2.0: Veritabanından dinamik yetki ve granülarite bilgisini çeker.
    Normalizasyon ile büyük/küçük harf duyarlılığı giderilmiştir.
    """
    try:
        with engine.connect() as conn:
            # rol_adi ve modul_anahtar için normalizasyon (isteğe bağlı, ama SQL'de LIKE veya LOWER daha güvenli olabilir)
            # Ancak biz Python tarafında veritabanındaki verileri normalize ederek karşılaştıracağız.
            sql = text("SELECT erisim_turu, sadece_kendi_bolumu, modul_adi FROM ayarlar_yetkiler WHERE rol_adi = :r")
            res = conn.execute(sql, {"r": rol_adi}).fetchall()
            
            target_key_norm = _normalize_string(modul_anahtar)
            
            for erisim, sinirli, m_adi in res:
                if _normalize_string(m_adi) == target_key_norm:
                    return erisim, (sinirli == 1)
            
            return "Yok", False
    except:
        return "Yok", False

@st.cache_data(ttl=300)
def sistem_modullerini_getir():
    """Anayasa v2.0: Aktif modül listesini dinamik olarak sırasıyla getirir.
    Sisteme Bootstrap mekanizması ile sıfır hardcode imkanı sağlar.
    """
    try:
        with engine.connect() as conn:
            # Sadece aktif modülleri alıp sırasına göre dizeriz
            sql = text("SELECT modul_etiketi FROM ayarlar_moduller WHERE aktif IS TRUE OR aktif = 1 ORDER BY sira_no ASC")
            res = conn.execute(sql).fetchall()
            if res:
                return [r[0] for r in res]
            else:
                return list(MODUL_ESLEME.keys()) # Hata durumunda güvenlik (Fallback)
    except:
        return list(MODUL_ESLEME.keys())

@st.cache_data(ttl=300)
def sistem_modullerini_ve_anahtarlarini_getir():
    """Anayasa v2.0: Modül etiketlerini ve anahtarlarını sözlük olarak getirir.
    UI tarafında (örn. Yetki Matrisi) id/etiket ayrımını doğru yönetmek için kullanılır.
    """
    try:
        with engine.connect() as conn:
            sql = text("SELECT modul_etiketi, modul_anahtari FROM ayarlar_moduller WHERE aktif IS TRUE OR aktif = 1 ORDER BY sira_no ASC")
            res = conn.execute(sql).fetchall()
            if res:
                return {r[0]: r[1] for r in res}
    except:
        pass
    return MODUL_ESLEME

# --- MEVCUT SİSTEM (MİRAS) ---

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

    # --- SIFIR HARDCODE: TEST YOLU ---
    if _dinamik_yetki_aktif_mi():
        modul_anahtari = _get_dinamik_modul_anahtari(menu_adi)
        erisim, _ = kullanici_yetkisi_getir_dinamik(user_rol, modul_anahtari)
        
        erisim_norm = _normalize_string(erisim)
        gereken_norm = _normalize_string(gereken_yetki)

        if gereken_norm == "GORUNTULE":
            return erisim_norm in ["GORUNTULE", "DUZENLE"]
        elif gereken_norm == "DUZENLE":
            return erisim_norm in ["DUZENLE"]
        return False

    # --- ESKİ SİSTEM: CANLI YOLU ---
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

    # --- SIFIR HARDCODE: TEST YOLU ---
    if _dinamik_yetki_aktif_mi():
        # Bu fonksiyon genellikle ürün tablolarında kullanılıyor (Üretim/KPI)
        # Hangi modülde olduğumuzu tahmin etmeye çalışalım veya genel bir kural işletelim
        # Varsayılan: Eğer yetki matrisinde 'sadece_kendi_bolumu' işaretliyse ve kullanıcı Admin değilse filtrele
        try:
            # Not: Bu kısım daha spesifik hale getirilecek, şimdilik test kullanıcısı için dinamik kural:
            with engine.connect() as conn:
                # Test kullanıcısının rolü için 'uretim_girisi' modülündeki kısıtı kontrol et
                res = conn.execute(text("""
                    SELECT sadece_kendi_bolumu FROM ayarlar_yetkiler 
                    WHERE rol_adi = :r AND modul_adi = 'uretim_girisi'
                """), {"r": user_rol}).fetchone()
                
                if res and res[0] and user_bolum:
                    # Dinamik Filtreleme: Hiçbir 'sevcanalbas' kontrolü yok!
                    if 'sorumlu_departman' in urun_df.columns:
                        mask_bos = urun_df['sorumlu_departman'].isna() | (urun_df['sorumlu_departman'] == '')
                        mask_eslesme = urun_df['sorumlu_departman'].astype(str).str.contains(str(user_bolum), case=False, na=False)
                        return urun_df[mask_bos | mask_eslesme]
                    elif 'uretim_bolumu' in urun_df.columns:
                        return urun_df[urun_df['uretim_bolumu'].astype(str).str.upper() == str(user_bolum).upper()]
        except:
            pass

    # --- ESKİ SİSTEM: CANLI YOLU ---
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
