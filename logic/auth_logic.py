import streamlit as st
import pandas as pd
from sqlalchemy import text
from logic.security.password import sifre_dogrula, sifre_hashle
import time
import json
from datetime import datetime
from logic.cache_manager import CACHE_TTL

# Veritabanı motoru (Anayasa v4: Artık fonksiyon içinde çağrılıyor)
# engine = get_engine() <-- Circular Import Önleyici (Lazy Load)

# 1. MODUL_ESLEME dict'i (Eski Sistem Bağlantısı - Normalize Edildi)
MODUL_ESLEME = {
    "🏠 Portal (Ana Sayfa)": "portal",
    "🏭 Üretim Girişi": "uretim_girisi",
    "🍩 KPI & Kalite Kontrol": "kpi_kontrol",
    "🛡️ GMP Denetimi": "gmp_denetimi",
    "🧼 Personel Hijyen": "personel_hijyen",
    "🧹 Temizlik Kontrol": "temizlik_kontrol",
    "📊 Kurumsal Raporlama": "kurumsal_raporlama",
    "❄️ Soğuk Oda Sıcaklıkları": "soguk_oda",
    "📦 MAP Üretim": "map_uretim",
    "📈 Yetkinlik & Performans": "performans_polivalans",
    "📁 QDMS": "qdms",
    "⚙️ Ayarlar": "ayarlar",
    "📜 Proje Anayasası": "anayasa"
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

@st.cache_data(ttl=CACHE_TTL['frequent'])
def _get_dinamik_modul_anahtari(menu_adi):
    """Menü etiketinden veritabanı anahtarını (modul_anahtari) bulur.
    Emojilerden ve Windows case-insensitive sorunlarından etkilenmemek için normalize edilmiş arama yapar.
    """
    try:
        from database.connection import get_engine
        with get_engine().connect() as conn:
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

                # Kademeli kontrol
                if clean_menu in target_etiket_norm or target_etiket_norm in clean_menu:
                    return anahtar
                if clean_menu_only_alnum and (clean_menu_only_alnum in target_etiket_norm or target_etiket_norm in clean_menu_only_alnum):
                    return anahtar
                if clean_menu == target_anahtar_norm or clean_menu_only_alnum == target_anahtar_norm:
                    return anahtar
            
            return menu_adi
    except Exception:
        return menu_adi

@st.cache_data(ttl=CACHE_TTL['frequent'])
def kullanici_yetkisi_getir_dinamik(rol_adi, modul_anahtar):
    """Anayasa v2.0: Veritabanından dinamik yetki ve granülarite bilgisini çeker.
    Normalizasyon ile büyük/küçük harf duyarlılığı giderilmiştir.
    """
    try:
        from database.connection import get_engine
        with get_engine().connect() as conn:
            # rol_adi ve modul_anahtar için normalizasyon (isteğe bağlı, ama SQL'de LIKE veya LOWER daha güvenli olabilir)
            # Ancak biz Python tarafında veritabanındaki verileri normalize ederek karşılaştıracağız.
            sql = text("SELECT erisim_turu, sadece_kendi_bolumu, modul_adi FROM ayarlar_yetkiler WHERE rol_adi = :r")
            res = conn.execute(sql, {"r": rol_adi}).fetchall()
            
            target_key_norm = _normalize_string(modul_anahtar)
            
            for erisim, sinirli, m_adi in res:
                if _normalize_string(m_adi) == target_key_norm:
                    return erisim, (sinirli == 1)
            
            return "Yok", False
    except Exception:
        return "Yok", False

@st.cache_data(ttl=CACHE_TTL['stable'])
def sistem_modullerini_getir(version="v4.1.8"):
    """Anayasa v2.0: Aktif modül listesini (etiket, anahtar) çifti olarak getirir."""
    try:
        from database.connection import get_engine
        with get_engine().connect() as conn:
            sql = text("SELECT modul_etiketi, modul_anahtari FROM ayarlar_moduller WHERE aktif = 1 ORDER BY sira_no ASC")
            res = conn.execute(sql).fetchall()
            if res:
                # v5.8.13: Aggressive Consolidation (Merging performance/competency variants)
                unique_modules = {}
                for etiket, anahtar in res:
                    u_key = str(anahtar).strip().lower()
                    # Performans, Polivalans veya Yetkinlik geçen tüm anahtarları birleştir
                    if any(x in u_key for x in ["performans", "polivalans", "yetkinlik"]):
                        u_key = "performans_polivalans"
                    
                    if u_key not in unique_modules:
                        unique_modules[u_key] = etiket
                    else:
                        # Eğer mevcut etiket emojili değilse ama yeni gelen emojili ise güncelle
                        has_emoji = any(ord(c) > 10000 for c in str(etiket))
                        prev_has_emoji = any(ord(c) > 10000 for c in str(unique_modules[u_key]))
                        if has_emoji and not prev_has_emoji:
                            unique_modules[u_key] = etiket
                return [(v, k) for k, v in unique_modules.items()]
            return [(k, v) for k, v in MODUL_ESLEME.items()]
    except Exception:
        return [(k, v) for k, v in MODUL_ESLEME.items()]

def _get_batch_yetki_haritasi(rol_adi):
    """Anayasa v3.2.7: Tüm yetkileri tek seferde çeker ve session_state'e kaydeder.
    Sorgu sayısını N'den 1'e düşürür.
    """
    rol_adi = str(rol_adi).upper().strip()
    
    # Session state önbelleğini kontrol et
    if 'batch_yetki_map' in st.session_state:
        saved_role, saved_map = st.session_state['batch_yetki_map']
        if saved_role == rol_adi:
            return saved_map

    # Cache yoksa veya rol değiştiyse DB'den çek
    yetki_map = {}
    try:
        from database.connection import get_engine
        target_rol_norm = _normalize_string(rol_adi)
        with get_engine().connect() as conn:
            # v5.8.0: Tüm yetkileri çek ve Python tarafında normalize ederek eşleştir (Zırhlı Yöntem)
            sql = text("SELECT rol_adi, modul_adi, erisim_turu, sadece_kendi_bolumu FROM ayarlar_yetkiler")
            all_perms = conn.execute(sql).fetchall()
            
            for r_db, m_adi, erisim, sinirli in all_perms:
                if _normalize_string(r_db) == target_rol_norm:
                    key = _normalize_string(m_adi)
                    yetki_map[key] = (erisim, (sinirli == 1))
    except Exception:
        pass

    # Kaydet ve dön
    st.session_state['batch_yetki_map'] = (rol_adi, yetki_map)
    return yetki_map

@st.cache_data(ttl=CACHE_TTL['stable'])
def sistem_modullerini_ve_anahtarlarini_getir():
    """Anayasa v2.0: Modül etiketlerini ve anahtarlarını sözlük olarak getirir.
    UI tarafında (örn. Yetki Matrisi) id/etiket ayrımını doğru yönetmek için kullanılır.
    """
    try:
        from database.connection import get_engine
        with get_engine().connect() as conn:
            sql = text("SELECT modul_etiketi, modul_anahtari FROM ayarlar_moduller WHERE aktif = 1 ORDER BY sira_no ASC")
            res = conn.execute(sql).fetchall()
            if res:
                return {r[0]: r[1] for r in res}
    except Exception:
        pass
    return MODUL_ESLEME

# --- ANAYASA v3.2: GÜVENLİK VE AUDIT FONKSİYONLARI ---

def audit_log_kaydet(islem, detay, kullanici=None, detay_json=None):
    """Anayasa v4.0.6: Global Activity Tracker. Logları otomatik metadata ile kaydeder."""
    try:
        # 1. Metadata Hazırla
        kullanici = kullanici or st.session_state.get('user', 'SISTEM')
        modul = st.session_state.get('active_module_key', 'bilinmiyor')
        ip, ua = _get_client_metadata()
        
        # 2. JSON Hazırla
        json_str = json.dumps(detay_json, ensure_ascii=False) if detay_json else None
        
        # 3. Yaz (Atomik)
        from database.connection import get_engine
        with get_engine().begin() as conn:
            sql = text("""
                INSERT INTO sistem_loglari 
                (islem_tipi, detay, modul, detay_json, ip_adresi, cihaz_bilgisi) 
                VALUES (:i, :d, :m, :j, :ip, :ua)
            """)
            conn.execute(sql, {
                "i": islem, "d": f"[{kullanici}] {detay}", 
                "m": modul, "j": json_str, "ip": ip, "ua": ua
            })
    except Exception as _e:
        print(f"audit_log_kaydet fallback: {_e}")

def _get_client_metadata():
    """İstemci IP ve User-Agent bilgilerini yakalar."""
    ip = "0.0.0.0"
    ua = "Bilinmiyor"
    try:
        headers = st.context.headers
        if headers:
            ua = headers.get("User-Agent", "Bilinmiyor")
            # X-Forwarded-For (Cloud) veya Remote-Addr
            ip = headers.get("X-Forwarded-For", headers.get("Remote-Addr", "0.0.0.0")).split(',')[0]
    except Exception:
        pass
    return ip, ua[:250]

# v6.1.9: Password logic extracted to logic.security.password
# Backward-compatible shim: sifre_dogrula, sifre_hashle are imported at top.

# --- MEVCUT SİSTEM (MİRAS) ---

@st.cache_data(ttl=CACHE_TTL['frequent']) # Anayasa v2.0 Uyumlu: 60 sn
def kullanici_yetkisi_getir(rol_adi, modul_adi):
    """Belirli rol için modül yetkisini veritabanından çeker (Case-Insensitive)"""
    try:
        from database.connection import get_engine
        with get_engine().connect() as conn:
            # Anayasa m.6: PostgreSQL büyük/küçük harf duyarlılığını önlemek için UPPER kullanılır.
            sql = text("""
                SELECT erisim_turu FROM ayarlar_yetkiler
                WHERE UPPER(rol_adi) = UPPER(:rol) AND UPPER(modul_adi) = UPPER(:modul)
            """)
            result = conn.execute(sql, {"rol": rol_adi, "modul": modul_adi}).fetchone()
            return result[0] if result else "Yok"
    except Exception:
        return "Yok"

# v3.1.5 - Secure Auth Logic
def kullanici_yetkisi_var_mi(menu_adi, gereken_yetki="Görüntüle", **kwargs):
    """Kullanıcının belirli modüle erişim yetkisini kontrol eder"""
    audit_log = kwargs.get('audit_log', True)
    user_rol_raw = st.session_state.get('user_rol', 'PERSONEL')
    from logic.zone_yetki import _normalize_rol
    user_rol = _normalize_rol(user_rol_raw)

    # --- ANAYASA MADDE 5: ADMIN BYPASS (GOD MODE) ---
    # Admin rolü veritabanı kısıtlamalarından muaftır.
    if user_rol == 'ADMIN':
        return True

    # --- ANAYASA MADDE 5: DİNAMİK YETKİ PATH (MANDATORY) ---
    res_status = False
    modul_anahtari = "Bilinmiyor"
    try:
        # S2-D: Eğer menu_adi zaten slug ise doğrudan kullan (Hız Kazancı)
        is_slug = menu_adi.islower() and " " not in menu_adi and any(c.isalpha() for c in menu_adi)
        modul_anahtari = menu_adi if is_slug else _get_dinamik_modul_anahtari(menu_adi)
        
        # v3.2.7: BATCH LOOKUP (Optimal: O(1))
        yetki_haritasi = _get_batch_yetki_haritasi(user_rol)
        target_key_norm = _normalize_string(modul_anahtari)
        
        erisim_data = yetki_haritasi.get(target_key_norm)
        
        # Fallback: Noktalı İ sorunu
        if not erisim_data and 'İ' in user_rol:
            yetki_haritasi = _get_batch_yetki_haritasi(user_rol.replace('İ', 'I'))
            erisim_data = yetki_haritasi.get(target_key_norm)

        if erisim_data:
            erisim, _ = erisim_data
            erisim_norm = _normalize_string(erisim)
            gereken_norm = _normalize_string(gereken_yetki)

            if gereken_norm == "GORUNTULE":
                res_status = erisim_norm in ["GORUNTULE", "DUZENLE"]
            elif gereken_norm == "DUZENLE":
                res_status = erisim_norm in ["DUZENLE"]
        else:
            res_status = False
    except Exception:
        res_status = False # Fail-Closed

    if not res_status and audit_log:
        audit_log_kaydet("ERISIM_REDDEDILDI", f"Yetkisiz erişim denemesi. Modül: {menu_adi} ({modul_anahtari}), Gereken: {gereken_yetki}")

    return res_status

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
            from database.connection import get_engine
            # Not: Bu kısım daha spesifik hale getirilecek, şimdilik test kullanıcısı için dinamik kural:
            with get_engine().connect() as conn:
                # Test kullanıcısının rolü için 'uretim_girisi' modülündeki kısıtı kontrol et
                res = conn.execute(text("""
                    SELECT sadece_kendi_bolumu FROM ayarlar_yetkiler 
                    WHERE rol_adi = :r AND modul_adi = 'uretim_girisi'
                """), {"r": user_rol}).fetchone()
                
                if res and res[0] and user_bolum:
                    # Dinamik Filtreleme: Yetki matrisinden gelen kısıta göre filtrele
                    if 'sorumlu_departman' in urun_df.columns:
                        mask_bos = urun_df['sorumlu_departman'].isna() | (urun_df['sorumlu_departman'] == '')
                        mask_eslesme = urun_df['sorumlu_departman'].astype(str).str.contains(str(user_bolum), case=False, na=False)
                        return urun_df[mask_bos | mask_eslesme]
                    elif 'uretim_bolumu' in urun_df.columns:
                        return urun_df[urun_df['uretim_bolumu'].astype(str).str.upper() == str(user_bolum).upper()]
        except Exception:
            pass

    # --- ESKİ SİSTEM: CANLI YOLU ---
    # 1. Admin, Üst Yönetim ve Kalite Ekibi her şeyi görsün
    if user_rol in ['ADMIN', 'YÖNETİM', 'GIDA MÜHENDİSİ'] or \
       'KALİTE' in user_rol or \
       'KALİTE' in str(user_bolum).upper() or \
       'LABORATUVAR' in str(user_bolum).upper():
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
        except Exception:
            return urun_df

    # 4. Eski Sistem Uyumluluğu
    elif 'uretim_bolumu' in urun_df.columns and user_bolum:
        return urun_df[urun_df['uretim_bolumu'].astype(str).str.upper() == str(user_bolum).upper()]

    return urun_df

# --- 13. ADAM: KALICI OTURUM (REMEMBER ME) YÖNETİMİ ---
import hashlib
import secrets
from datetime import datetime, timedelta

def kalici_oturum_olustur(engine, kullanici_id: int, cihaz_bilgisi: str = None, ip_adresi: str = None, son_modul: str = 'portal') -> str:
    """Yeni bir kalıcı oturum oluşturur, çerez için ham token döner."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    gecerlilik = datetime.now() + timedelta(days=7) # Emre Bey: 7 gün yeterli
    
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO sistem_oturum_izleri (token_hash, kullanici_id, cihaz_bilgisi, ip_adresi, gecerlilik_ts, son_modul)
            VALUES (:th, :kid, :cb, :ip, :gt, :sm)
        """), {"th": token_hash, "kid": kullanici_id, "cb": cihaz_bilgisi, "ip": ip_adresi, "gt": gecerlilik, "sm": son_modul})
    
    return raw_token

def kalici_oturum_dogrula(engine, raw_token: str, cihaz_bilgisi: str = None) -> dict | None:
    """Çerezdeki token'ı doğrular ve kullanıcı bilgilerini döner."""
    if not raw_token: return None
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    sql = text("""
        SELECT p.*, b.bolum_adi as bolum, s.son_modul 
        FROM sistem_oturum_izleri s
        JOIN ayarlar_kullanicilar p ON s.kullanici_id = p.id
        LEFT JOIN ayarlar_bolumler b ON p.departman_id = b.id
        WHERE s.token_hash = :th 
          AND s.gecerlilik_ts > NOW()
          AND (s.cihaz_bilgisi = :cb OR :cb IS NULL)
    """)
    
    with engine.connect() as conn:
        res = conn.execute(sql, {"th": token_hash, "cb": cihaz_bilgisi}).fetchone()
        if res:
            # Oturum başarılı, son erişim zamanını güncelle
            conn.execute(text("UPDATE sistem_oturum_izleri SET son_erisim_ts = NOW() WHERE token_hash = :th"), {"th": token_hash})
            # Row'u dict'e çevir (SQLAlchemy 2.x)
            cols = res._fields
            return dict(zip(cols, res))
    return None

def oturum_modul_guncelle(engine, raw_token: str, modul_key: str):
    """Kullanıcının aktif olduğu son modülü veritabanında günceller."""
    if not raw_token or not modul_key: return
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    try:
        with engine.begin() as conn:
            conn.execute(text("UPDATE sistem_oturum_izleri SET son_modul = :m, son_erisim_ts = NOW() WHERE token_hash = :th"), 
                         {"m": modul_key, "th": token_hash})
    except Exception:
        pass # Migration henüz yapılmamış olabilir

def kalici_oturum_sil(engine, raw_token: str):
    """Oturum izini veritabanından siler."""
    if not raw_token: return
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM sistem_oturum_izleri WHERE token_hash = :th"), {"th": token_hash})
