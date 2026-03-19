import streamlit as st
import pandas as pd
from sqlalchemy import text
from passlib.hash import bcrypt
import time
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
    "📦 MAP Üretim": "MAP Üretim",
    "📊 Performans & Polivalans": "Performans & Polivalans",
    "📁 QDMS": "qdms",
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

def normalize_role_string(r):
    """Rol isimlerini merkezi standarda (BÜYÜK HARF ve ASCII-ish) dönüştürür."""
    if not r: return "PERSONEL"
    # Bilinen yazım hataları için manuel map
    corrections = {
        "KALITE SORUMLSU": "KALITE SORUMLUSU",
        "KALİTE SORUMLSU": "KALITE SORUMLUSU",
        "KALİTE SORUMLUSU": "KALITE SORUMLUSU"
    }
    res = _normalize_string(r)
    return corrections.get(res, res)

def _dinamik_yetki_aktif_mi():
    """Anayasa v2.1: Tüm kullanıcılar için dinamik yetki sistemini aktif eder.
    Böylece emoji ve karakter (İ/I) uyumsuzlukları merkezi normalizasyon ile çözülür.
    """
    return True

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
                # if _dinamik_yetki_aktif_mi():
                #     print(f"DEBUG: Comparing '{clean_menu}' with Label:'{target_etiket_norm}' Key:'{target_anahtar_norm}'")

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
            
            # if _dinamik_yetki_aktif_mi(): print(f"DEBUG: NO MATCH FOR {menu_adi}")
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
            sql = text("SELECT modul_etiketi FROM ayarlar_moduller WHERE aktif = 1 ORDER BY sira_no ASC")
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
            sql = text("SELECT modul_etiketi, modul_anahtari FROM ayarlar_moduller WHERE aktif = 1 ORDER BY sira_no ASC")
            res = conn.execute(sql).fetchall()
            if res:
                return {r[0]: r[1] for r in res}
    except:
        pass
    return MODUL_ESLEME

# --- ANAYASA v3.2: GÜVENLİK VE AUDIT FONKSİYONLARI ---

def audit_log_kaydet(islem, detay, kullanici=None):
    """Anayasa v3.2: Güvenlik loglarını sessizce (fail-silent) kaydeder."""
    try:
        if kullanici is None:
            kullanici = st.session_state.get('user', 'SISTEM')
        
        # Engine.begin() ile atomik işlem garantisi
        with engine.begin() as conn:
            sql = text("INSERT INTO sistem_loglari (islem_tipi, detay, zaman) VALUES (:i, :d, CURRENT_TIMESTAMP)")
            conn.execute(sql, {"i": islem, "d": f"[{kullanici}] {detay}"})
    except:
        # Sigorta kuralı: Log hatası ana akışı bozamaz.
        pass

def _plaintext_fallback_izni_var_mi():
    """Anayasa v3.2: Plain-text şifre desteğinin hala geçerli olup olmadığını kontrol eder."""
    try:
        with engine.connect() as conn:
            # Sistem parametrelerinden ayarları çek
            sql = text("SELECT param_adi, param_degeri FROM sistem_parametreleri WHERE param_adi IN ('plaintext_fallback_aktif', 'fallback_bitis_tarihi')")
            res = conn.execute(sql).fetchall()
            ayarlar = {r[0]: r[1] for r in res}
            
            aktif = ayarlar.get('plaintext_fallback_aktif', 'True').lower() == 'true'
            if not aktif: return False
            
            # Veritabanında yoksa kod içindeki güvenli tarihi (2026-06-15) baz al
            bitis_str = ayarlar.get('fallback_bitis_tarihi', '2026-06-15')
            bitis_tarihi = pd.to_datetime(bitis_str)
            
            # Bugünün tarihi ile karşılaştır
            bugun = pd.Timestamp.now().normalize()
            return bugun <= bitis_tarihi
    except:
        return True # Hata durumunda (tablo yok vb.) geçiş süreci için izin ver

def get_fallback_info():
    """Anayasa v3.2: Grace period bitiş tarihini ve durumunu döner."""
    try:
        with engine.connect() as conn:
            sql = text("SELECT param_degeri FROM sistem_parametreleri WHERE param_adi = 'fallback_bitis_tarihi'")
            res = conn.execute(sql).scalar()
            return str(res) if res else "2026-06-15"
    except:
        return "2026-06-15"

def sifre_hashle(plain_sifre):
    """Şifreyi bcrypt ile hashler."""
    return bcrypt.hash(str(plain_sifre))

def _bcrypt_formatinda_mi(s):
    """Şifrenin bcrypt hash formatında ($2b$...) olup olmadığını kontrol eder."""
    return str(s).startswith("$2b$") or str(s).startswith("$2a$")

def sifre_dogrula(girilen_sifre, db_sifre, kullanici_adi=None):
    """Dual-Validation: Hem plain-text hem bcrypt destekler, otomatik migration sağlar."""
    if not db_sifre: return False
    
    gecerli = False
    if _bcrypt_formatinda_mi(db_sifre):
        try:
            gecerli = bcrypt.verify(girilen_sifre, db_sifre)
        except:
            gecerli = False
    else:
        # Fallback: Plain-text karşılaştırma (Anayasa v3.2 Grace Period kontrolü ile)
        if _plaintext_fallback_izni_var_mi():
            gecerli = (str(girilen_sifre) == str(db_sifre))
            
            # Eğer plain-text ile doğrulandıysa, sessizce hashleme sırasına al (Lazy Migration)
            if gecerli and kullanici_adi:
                _sifreyi_hashle_ve_guncelle(kullanici_adi, girilen_sifre)
        else:
            # Vakti geçmiş plain-text şifre denemesi
            audit_log_kaydet("FALLBACK_EXPIRED", f"Süresi dolmuş düz metin şifre denemesi engellendi. Kullanıcı: {kullanici_adi}", kullanici_adi)
            gecerli = False
            
    if not gecerli:
        audit_log_kaydet("GIRIS_BASARISIZ", f"Hatalı şifre denemesi (User: {kullanici_adi})", kullanici_adi)
        
    return gecerli

def _sifreyi_hashle_ve_guncelle(kullanici_adi, plain_sifre):
    """Şifreyi atomik ve güvenli bir şekilde bcrypt hash'ine dönüştürür."""
    try:
        yeni_hash = bcrypt.hash(plain_sifre)
        
        # Bariyer: Yazmadan önce hash geçerliliğini doğrula (Risk 2)
        if not bcrypt.verify(plain_sifre, yeni_hash):
            return False
            
        with engine.begin() as conn:
            # Idempotent güncelleme: Sadece şifre değişmişse yaz
            sql = text("UPDATE personel SET sifre = :h WHERE kullanici_adi = :k AND (sifre != :h OR (SELECT 1 FROM personel WHERE kullanici_adi = :k AND sifre NOT LIKE '$2%'))")
            # Basitleştirilmiş: Sadece şifre bcrypt değilse güncelle (Lazy Migration)
            sql = text("UPDATE personel SET sifre = :h WHERE kullanici_adi = :k AND (sifre IS NULL OR sifre NOT LIKE '$2%')")
            conn.execute(sql, {"h": yeni_hash, "k": kullanici_adi})
            audit_log_kaydet("SIFRE_HASH_MIGRATION", "Şifre plain-text'ten bcrypt'e taşındı.", kullanici_adi)
        return True
    except Exception as e:
        audit_log_kaydet("HASH_HATA", f"Şifre hashlenirken hata oluştu: {str(e)}", kullanici_adi)
        return False

# --- MEVCUT SİSTEM (MİRAS) ---

@st.cache_data(ttl=60) # Anayasa v2.0 Uyumlu: 60 sn
def kullanici_yetkisi_getir(rol_adi, modul_adi):
    """Belirli rol için modül yetkisini veritabanından çeker (Case-Insensitive)"""
    try:
        with engine.connect() as conn:
            # Anayasa m.6: PostgreSQL büyük/küçük harf duyarlılığını önlemek için UPPER kullanılır.
            sql = text("""
                SELECT erisim_turu FROM ayarlar_yetkiler
                WHERE UPPER(rol_adi) = UPPER(:rol) AND UPPER(modul_adi) = UPPER(:modul)
            """)
            result = conn.execute(sql, {"rol": rol_adi, "modul": modul_adi}).fetchone()
            return result[0] if result else "Yok"
    except:
        return "Yok"

# v3.1.5 - Secure Auth Logic
def kullanici_yetkisi_var_mi(menu_adi, gereken_yetki="Görüntüle", **kwargs):
    """Kullanıcının belirli modüle erişim yetkisini kontrol eder"""
    audit_log = kwargs.get('audit_log', True)
    user_rol = str(st.session_state.get('user_rol', 'PERSONEL')).upper().strip()

    # --- ANAYASA MADDE 5: ADMIN BYPASS (GOD MODE) ---
    # Admin rolü veritabanı kısıtlamalarından muaftır.
    if user_rol == 'ADMIN':
        return True

    # --- ANAYASA MADDE 5: DİNAMİK YETKİ PATH (MANDATORY) ---
    res_status = False
    modul_anahtari = "Bilinmiyor"
    try:
        modul_anahtari = _get_dinamik_modul_anahtari(menu_adi)
        erisim, _ = kullanici_yetkisi_getir_dinamik(user_rol, modul_anahtari)
        
        # Fallback: Eğer Noktalı İ sorunu varsa I ile tekrar dene
        if erisim == "Yok" and 'İ' in user_rol:
            erisim, _ = kullanici_yetkisi_getir_dinamik(user_rol.replace('İ', 'I'), modul_anahtari)

        erisim_norm = _normalize_string(erisim)
        gereken_norm = _normalize_string(gereken_yetki)

        if gereken_norm == "GORUNTULE":
            res_status = erisim_norm in ["GORUNTULE", "DUZENLE"]
        elif gereken_norm == "DUZENLE":
            res_status = erisim_norm in ["DUZENLE"]
    except:
        res_status = False # Fail-Closed

    if not res_status and audit_log:
        audit_log_kaydet("ERISIM_REDDEDILDI", f"Yetkisiz erişim denemesi. Modül: {menu_adi} ({modul_anahtari}), Gereken: {gereken_yetki}")

    return res_status
    
    # ESKİ SİSTEM FALLBACK (Sadece çok kritik hatalarda)
    modul_adi_eski = MODUL_ESLEME.get(menu_adi, menu_adi)
    erisim_eski = kullanici_yetkisi_getir(user_rol, modul_adi_eski)
    if gereken_yetki == "Görüntüle":
        return erisim_eski.upper() in ["GÖRÜNTÜLE", "DÜZENLE"]
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
