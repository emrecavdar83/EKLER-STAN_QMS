# v3.1.9 - Performance Optimized Data Fetcher
import streamlit as st
import pandas as pd
from sqlalchemy import text
# from database.connection import get_engine # v6.8.9: Lazy Load and circular fix
from datetime import datetime
from constants import get_position_name
from logic.cache_manager import CACHE_TTL

# Veritabanı motorunu al (Anayasa v4: Artık fonksiyon içinde çağrılıyor)
# engine = get_engine() <-- Circular Import Önleyici (Lazy Load)

def robust_id_clean(v):
    if pd.isnull(v) or str(v).strip() in ['0', '0.0', 'None', 'nan', '', '0.']: return None
    try: return int(float(v))
    except: return None

def get_hierarchy_flat(df, parent_id=None, prefix=""):
    """
    Dataframe içinden hiyerarşik isim listesi döndürür: ['Üretim', 'Üretim > Sos Ekleme']
    """
    items = []
    # ana_departman_id kolonuna göre hiyerarşi kur
    children = df[df['ana_departman_id'].fillna(0) == (parent_id if parent_id else 0)]
    
    for _, row in children.iterrows():
        current_name = f"{prefix}{row['bolum_adi']}"
        items.append(current_name)
        # Altları ara
        items.extend(get_hierarchy_flat(df, row['id'], f"{current_name} > "))
    return items

@st.cache_data(ttl=CACHE_TTL['stable']) # Hız için cache (Standart: Stable)
def run_query(query, params=None, where=None):
    """
    Veritabanında SQL sorgusu çalıştırır ve sonuçları DataFrame olarak döndürür.
    where: Opsiyonel filtre cümlesi (örn: 'tarih = :t')
    """
    final_query = str(query)
    if where:
        if "WHERE" in final_query.upper():
            final_query += f" AND {where}"
        else:
            final_query += f" WHERE {where}"
            
    # v6.3.2: Manual Fetch Bypass (Pandas 3.13 / SQLAlchemy 2.0.x TypeError Fix)
    from database.connection import get_engine
    with get_engine().connect() as conn:
        res = conn.execute(text(final_query), params or {})
        df = pd.DataFrame(res.fetchall(), columns=res.keys())
        return df

@st.cache_data(ttl=CACHE_TTL['static']) # Emekli fonksiyon (Standart: Static)
def get_user_roles():
    """ANAYASA v3.0: Bu fonksiyon hardcoded roller içerdiği için EMEKLİ EDİLMİŞTİR.
    Yetki kontrolleri artık logic.auth_logic içindeki dinamik fonksiyonlarla yapılır.
    """
    return [], []

@st.cache_data(ttl=CACHE_TTL['stable'])
def get_department_tree(filter_tur=None):
    """
    v6.1: LEGACY BRIDGE - Redirects to qms_departmanlar.
    """
    try:
        # Use QMS table but return bolum_adi for compatibility
        df_dept = run_query("SELECT id, ad as bolum_adi, ust_id as ana_departman_id FROM qms_departmanlar WHERE durum = 'AKTİF' ORDER BY sira_no")
        
        if df_dept.empty: return []
        hierarchy_list = []

        def build(parent_id, current_path, level):
            if level > 20: return # v6.3: Updated to 20 levels
            
            mask = df_dept['ana_departman_id'].isnull() if parent_id is None else df_dept['ana_departman_id'] == parent_id
            current = df_dept[mask]

            for _, row in current.iterrows():
                new_path = f"{current_path} > {row['bolum_adi']}" if current_path else row['bolum_adi']
                hierarchy_list.append(new_path)
                build(row['id'], new_path, level + 1)

        build(None, "", 1)
        return hierarchy_list
    except Exception:
        return []

@st.cache_data(ttl=CACHE_TTL['stable'])
def get_qms_department_options_hierarchical():
    """QMS Departmanlarını hiyerarşik Selectbox formatında döndürür."""
    # v6.3.4: Manual Fetch Bypass & Robust Fallback
    options = {0: "🏢 Tüm Bölümler / Fabrika"}
    try:
        sql = "SELECT id, ad, ust_id FROM qms_departmanlar WHERE durum = 'AKTİF' ORDER BY sira_no"
        from database.connection import get_engine
        with get_engine().connect() as conn:
            res = conn.execute(text(sql))
            df = pd.DataFrame(res.fetchall(), columns=res.keys())
        
        if df.empty: return options
        
        def build(parent_id, prefix, level):
            if level > 20: return
            
            # v6.3.5: Robust mask handling (Pandas 2.x compatibility)
            if parent_id is None or parent_id == 0:
                mask = df['ust_id'].isnull() | (df['ust_id'] == 0)
            else:
                mask = df['ust_id'] == parent_id
                
            for _, row in df[mask].iterrows():
                label = f"{prefix}{row['ad']}".strip()
                options[row['id']] = label
                build(row['id'], f"{prefix}.. ", level + 1)
        
        build(None, "", 1)
        return options
    except Exception as e:
        st.error(f"❌ Hiyerarşi Hatası: {e}")
        return options

@st.cache_data(ttl=CACHE_TTL['stable'])
def get_qms_department_tree():
    """Sadece isim listesi olarak ağaç yapısı döndürür."""
    try:
        df = run_query("SELECT id, ad, ust_id FROM qms_departmanlar WHERE durum = 'AKTİF' ORDER BY sira_no")
        tree = []
        
        def build(parent_id, prefix, level):
            mask = df['ust_id'].isnull() if parent_id is None else df['ust_id'] == parent_id
            for _, row in df[mask].iterrows():
                tree.append(f"{prefix}🏢 {row['ad']}")
                build(row['id'], prefix + "    ", level + 1)
        
        build(None, "", 1)
        return tree
    except: return []

@st.cache_data(ttl=CACHE_TTL['stable'])
def get_department_options_hierarchical():
    return get_qms_department_options_hierarchical()

@st.cache_data(ttl=CACHE_TTL['stable'])
def get_all_sub_department_ids(parent_id):
    """v6.1: LEGACY BRIDGE - Redirects to qms_departmanlar sub-tree."""
    try:
        df_dept = run_query("SELECT id, ust_id FROM qms_departmanlar WHERE durum = 'AKTİF'")
        ids = [parent_id]

        def find_children(p_id):
            children = df_dept[df_dept['ust_id'] == p_id]['id'].tolist()
            for child in children:
                ids.append(child)
                find_children(child)

        find_children(parent_id)
        return ids
    except Exception:
        return [parent_id]

@st.cache_data(ttl=CACHE_TTL['critical'])
def get_personnel_hierarchy():
    """v6.8.9: Targeted Source - Hierarchy now pulls from the main Personnel view."""
    try:
        df = run_query(
            "SELECT p.id, p.ad_soyad, p.gorev, p.rol, "
            "COALESCE(d.ad, 'Tanimsiz') as departman_adi, "
            "p.kullanici_adi, p.durum, "
            "COALESCE(p.vardiya, 'GUNDUZ VARDIYASI') as vardiya, "
            "COALESCE(p.pozisyon_seviye, 5) as pozisyon_seviye, "
            "p.yonetici_id, p.qms_departman_id as departman_id, "
            "p.operasyonel_bolum_id "
            "FROM tum_personel p "
            "LEFT JOIN qms_departmanlar d ON p.qms_departman_id = d.id "
            "WHERE p.ad_soyad IS NOT NULL"
        )
    except Exception:
        return pd.DataFrame()
    
    # ... (Rest of logic remains the same)
    if df.empty: return df
    if 'pozisyon_adi' not in df.columns and 'pozisyon_seviye' in df.columns:
        df['pozisyon_adi'] = df['pozisyon_seviye'].apply(lambda x: get_position_name(int(x)) if pd.notnull(x) else 'Bilinmiyor')
    if 'pozisyon_seviye' in df.columns:
        df['pozisyon_seviye'] = pd.to_numeric(df['pozisyon_seviye'], errors='coerce').fillna(5).astype(int)
    if 'departman_id' in df.columns:
        df['departman_id'] = pd.to_numeric(df['departman_id'], errors='coerce').fillna(0).astype(int)
    if 'durum' in df.columns:
        df = df[df['durum'].astype(str).str.strip().str.upper() == 'AKTİF']
    return df

@st.cache_data(ttl=CACHE_TTL['frequent'])
def cached_veri_getir(tablo_adi):
    """Tablo adına göre önbelleğe alınmış veri getirir."""
    queries = {
        "ayarlar_kullanicilar": "SELECT * FROM ayarlar_kullanicilar WHERE kullanici_adi IS NOT NULL ORDER BY ad_soyad ASC",
        "Ayarlar_Personel_V2": (
            "SELECT p.id, p.ad_soyad, p.kullanici_adi, p.rol, p.durum, "
            "p.qms_departman_id as departman_id, p.pozisyon_seviye, "
            "COALESCE(p.vardiya, 'GUNDUZ VARDIYASI') as vardiya, "
            "d.ad as bolum, p.gorev, p.ise_giris_tarihi, p.telefon_no, p.servis_duragi, "
            "p.yonetici_id, p.operasyonel_bolum_id, p.ikincil_yonetici_id "
            "FROM personel p "
            "LEFT JOIN qms_departmanlar d ON p.qms_departman_id = d.id "
            "ORDER BY CASE WHEN p.pozisyon_seviye ~ '^[0-9]+$' THEN CAST(p.pozisyon_seviye AS INTEGER) ELSE 9 END ASC, p.ad_soyad ASC"
        ),
        "Ayarlar_Urunler": "SELECT * FROM ayarlar_urunler",
        "Depo_Giris_Kayitlari": "SELECT id, tarih, irsaliye_no, tedarikçi, urun_adi, miktar, birim FROM depo_giris_kayitlari ORDER BY id DESC LIMIT 50",
        "Ayarlar_Fabrika_Personel": "SELECT * FROM ayarlar_kullanicilar WHERE ad_soyad IS NOT NULL ORDER BY pozisyon_seviye ASC, ad_soyad ASC",
        "Ayarlar_Temizlik_Plani": "SELECT id, bolum_id, ekipman_adi, periyot, metot, kimyasal FROM ayarlar_temizlik_plani",
        "Tanim_Bolumler": "SELECT id, ad as bolum_adi, ust_id as ana_departman_id, durum FROM qms_departmanlar ORDER BY id",
        "Tanim_Ekipmanlar": "SELECT id, ad, kod, bolum_id FROM tanim_ekipmanlar",
        "Tanim_Metotlar": "SELECT id, ad, detay FROM tanim_metotlar",
        "Kimyasal_Envanter": "SELECT id, ad, tip, risk_grubu FROM kimyasal_envanter ORDER BY id",
        "GMP_Soru_Havuzu": "SELECT id, soru_metni, kategori, risk_puani FROM gmp_soru_havuzu",
        "Ayarlar_Bolumler": "SELECT id, ad as bolum_adi, ust_id as ana_departman_id, sira_no, durum FROM qms_departmanlar WHERE durum = 'AKTİF' ORDER BY sira_no",
        "soguk_odalar": "SELECT * FROM soguk_odalar ORDER BY id ASC"
    }

    sql = queries.get(tablo_adi)
    if not sql: return pd.DataFrame()

    try:
        # v3.1: Veri boyutuna göre akıllı limit
        if "kayitlari" in tablo_adi.lower() or "veriler" in tablo_adi.lower():
             sql += " ORDER BY id DESC LIMIT 1000"
             
        df = run_query(sql)
        df.columns = [c.lower().strip() for c in df.columns]
        return df
    except Exception:
        return pd.DataFrame()

def veri_getir(tablo_adi):
    """cached_veri_getir için sarmalayıcı fonksiyon."""
    return cached_veri_getir(tablo_adi)

@st.cache_data(ttl=CACHE_TTL['stable']) # v3.1.9: Raporlar için yüksek performanslı cache
def get_personnel_shift(personel_id, target_date=None):
    """Personelin vardiya bilgisini döndürür."""
    if target_date is None:
        target_date = datetime.now().date()

    try:
        from database.connection import get_engine
        sql = text("""
            SELECT vardiya FROM personel_vardiya_programi
            WHERE personel_id = :pid
            AND :tdate BETWEEN baslangic_tarihi AND bitis_tarihi
            ORDER BY id DESC LIMIT 1
        """)
        with get_engine().connect() as conn:
            res = conn.execute(sql, {"pid": personel_id, "tdate": target_date}).fetchone()
            if res:
                return res[0]

        sql_legacy = text("SELECT vardiya FROM ayarlar_kullanicilar WHERE id = :pid")
        with get_engine().connect() as conn:
            res_legacy = conn.execute(sql_legacy, {"pid": personel_id}).fetchone()
            if res_legacy and res_legacy[0]:
                return res_legacy[0]

    except Exception:
        pass

    return "GÜNDÜZ VARDİYASI"

@st.cache_data(ttl=CACHE_TTL['stable']) # v3.1.9: Raporlar için yüksek performanslı cache
def is_personnel_off(personel_id, target_date=None):
    """Personelin izin durumunu döndürür."""
    if target_date is None:
        target_date = datetime.now().date()

    day_name_tr_map = {
        0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe",
        4: "Cuma", 5: "Cumartesi", 6: "Pazar"
    }
    today_name = day_name_tr_map[target_date.weekday()]

    try:
        from database.connection import get_engine
        sql = text("""
            SELECT izin_gunleri FROM personel_vardiya_programi
            WHERE personel_id = :pid
            AND :tdate BETWEEN baslangic_tarihi AND bitis_tarihi
            ORDER BY id DESC LIMIT 1
        """)
        with get_engine().connect() as conn:
            res = conn.execute(sql, {"pid": personel_id, "tdate": target_date}).fetchone()
            if res and res[0]:
                return today_name in res[0]

        sql_legacy = text("SELECT izin_gunu FROM ayarlar_kullanicilar WHERE id = :pid")
        with get_engine().connect() as conn:
            res_legacy = conn.execute(sql_legacy, {"pid": personel_id}).fetchone()
            if res_legacy and res_legacy[0]:
                return res_legacy[0] == today_name

    except Exception:
        pass

    return False
