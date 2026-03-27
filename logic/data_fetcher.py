# v3.1.9 - Performance Optimized Data Fetcher
import streamlit as st
import pandas as pd
from sqlalchemy import text
from database.connection import get_engine
from datetime import datetime
from constants import get_position_name

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

@st.cache_data(ttl=600) # Hız için 10 dk cache (v3.1)
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
            
    with get_engine().connect() as conn:
        return pd.read_sql(text(final_query), conn, params=params)

@st.cache_data(ttl=3600) # Rol bazlı listeler 1 saat cache'de kalsın
def get_user_roles():
    """ANAYASA v3.0: Bu fonksiyon hardcoded roller içerdiği için EMEKLİ EDİLMİŞTİR.
    Yetki kontrolleri artık logic.auth_logic içindeki dinamik fonksiyonlarla yapılır.
    """
    return [], []

@st.cache_data(ttl=600)
def get_department_tree(filter_tur=None):
    """
    Veritabanından departmanları çekip hiyerarşik isim listesi döndürür (Örn: Üretim > Temizlik).
    """
    try:
        try:
            df_dept = run_query("SELECT id, bolum_adi, ana_departman_id, tur FROM ayarlar_bolumler WHERE aktif = 1 ORDER BY sira_no")
        except Exception:
            df_dept = run_query("SELECT id, bolum_adi, ana_departman_id FROM ayarlar_bolumler WHERE aktif = 1 ORDER BY sira_no")
            df_dept['tur'] = None

        if df_dept.empty: return []

        hierarchy_list = []

        def build(parent_id, current_path, level):
            if level > 5: return

            if parent_id is None:
                current = df_dept[df_dept['ana_departman_id'].isnull() | (df_dept['ana_departman_id'] == 0) | (df_dept['ana_departman_id'].isna())]
            else:
                current = df_dept[df_dept['ana_departman_id'] == parent_id]

            for _, row in current.iterrows():
                new_path = f"{current_path} > {row['bolum_adi']}" if current_path else row['bolum_adi']

                if not filter_tur or row['tur'] == filter_tur:
                    hierarchy_list.append(new_path)

                build(row['id'], new_path, level + 1)

        build(None, "", 1)

        if not hierarchy_list and filter_tur:
            return get_department_tree(None)

        return hierarchy_list
    except Exception:
        return []

@st.cache_data(ttl=600)
def get_department_options_hierarchical():
    """Selectbox için hiyerarşik (Dictionary) yapı döndürür: {id: '.. ↳ Alt'}"""
    try:
        df_dept = run_query("SELECT id, bolum_adi, ana_departman_id FROM ayarlar_bolumler WHERE aktif = 1 ORDER BY sira_no")
        if df_dept.empty:
            return {0: "- Seçiniz -"}

        options = {0: "- Seçiniz -"}

        def add_to_options(parent_id, level=0):
            if parent_id is None:
                current = df_dept[df_dept['ana_departman_id'].isnull() | (df_dept['ana_departman_id'] == 0)]
            else:
                current = df_dept[df_dept['ana_departman_id'] == parent_id]

            for _, row in current.iterrows():
                d_id = row['id']
                name = row['bolum_adi']
                indent = ".. " * level
                marker = "↳ " if level > 0 else ""
                full_name = f"{indent}{marker}{name}"
                options[d_id] = full_name
                add_to_options(d_id, level + 1)

        add_to_options(None)
        return options
    except Exception:
        return {0: "- Seçiniz -"}

@st.cache_data(ttl=600)
def get_all_sub_department_ids(parent_id):
    """Verilen departman ID ve altındaki tüm departman ID'lerini listeler."""
    try:
        df_dept = run_query("SELECT id, ana_departman_id FROM ayarlar_bolumler WHERE aktif = 1")
        ids = [parent_id]

        def find_children(p_id):
            children = df_dept[df_dept['ana_departman_id'] == p_id]['id'].tolist()
            for child in children:
                ids.append(child)
                find_children(child)

        find_children(parent_id)
        return ids
    except Exception:
        return [parent_id]

@st.cache_data(ttl=3600) # Personel hiyerarşisi 1 saat cache (v3.1)
def get_personnel_hierarchy():
    """Personel hiyerarşisini ve detaylarını döndürür."""
    try:
        df = pd.read_sql("""
            SELECT
                p.id, p.ad_soyad, p.gorev, p.rol,
                COALESCE(d.bolum_adi, 'Tanımsız') as departman_adi,
                p.kullanici_adi, p.durum, p.vardiya,
                COALESCE(p.pozisyon_seviye, 5) as pozisyon_seviye,
                p.yonetici_id, p.departman_id
            FROM personel p
            LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
            WHERE p.ad_soyad IS NOT NULL
        """, get_engine())
    except Exception:
        return pd.DataFrame()

    if df.empty:
        return df

    if 'departman' in df.columns and 'departman_adi' not in df.columns:
        df = df.rename(columns={'departman': 'departman_adi'})

    if 'pozisyon_adi' not in df.columns and 'pozisyon_seviye' in df.columns:
        df['pozisyon_adi'] = df['pozisyon_seviye'].apply(lambda x: get_position_name(int(x)) if pd.notnull(x) else 'Bilinmiyor')

    if 'pozisyon_seviye' in df.columns:
        df['pozisyon_seviye'] = pd.to_numeric(df['pozisyon_seviye'], errors='coerce').fillna(5).astype(int)

    if 'departman_id' in df.columns:
        df['departman_id'] = pd.to_numeric(df['departman_id'], errors='coerce').fillna(0).astype(int)

    if 'ad_soyad' in df.columns:
        try:
            df = df.sort_values(['pozisyon_seviye', 'departman_id', 'ad_soyad'])
        except Exception:
            pass

    if 'durum' in df.columns:
        df = df[df['durum'].astype(str).str.strip().str.upper() == 'AKTİF']

    return df

@st.cache_data(ttl=60)
def cached_veri_getir(tablo_adi):
    """Tablo adına göre önbelleğe alınmış veri getirir."""
    queries = {
        "personel": "SELECT id, ad_soyad, kullanici_adi, rol, durum, departman_id, pozisyon_seviye FROM personel WHERE ad_soyad IS NOT NULL ORDER BY pozisyon_seviye ASC, ad_soyad ASC",
        "Ayarlar_Personel_V2": "SELECT p.id, p.ad_soyad, p.kullanici_adi, p.sifre, p.rol, p.durum, p.departman_id, p.pozisyon_seviye, p.vardiya, d.bolum_adi as bolum FROM personel p LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id WHERE p.kullanici_adi IS NOT NULL ORDER BY p.pozisyon_seviye ASC, p.ad_soyad ASC",
        "Ayarlar_Urunler": "SELECT id, urun_adi, urun_kodu, aktif FROM ayarlar_urunler",
        "Depo_Giris_Kayitlari": "SELECT id, tarih, irsaliye_no, tedarikçi, urun_adi, miktar, birim FROM depo_giris_kayitlari ORDER BY id DESC LIMIT 50",
        "Ayarlar_Fabrika_Personel": "SELECT id, ad_soyad, kullanici_adi, rol, durum, departman_id, pozisyon_seviye FROM personel WHERE ad_soyad IS NOT NULL ORDER BY pozisyon_seviye ASC, ad_soyad ASC",
        "Ayarlar_Temizlik_Plani": "SELECT id, bolum_id, ekipman_adi, periyot, metot, kimyasal FROM ayarlar_temizlik_plani",
        "Tanim_Bolumler": "SELECT id, bolum_adi, ana_departman_id, aktif FROM ayarlar_bolumler ORDER BY id",
        "Tanim_Ekipmanlar": "SELECT id, ad, kod, bolum_id FROM tanim_ekipmanlar",
        "Tanim_Metotlar": "SELECT id, ad, detay FROM tanim_metotlar",
        "Kimyasal_Envanter": "SELECT id, ad, tip, risk_grubu FROM kimyasal_envanter ORDER BY id",
        "GMP_Soru_Havuzu": "SELECT id, soru_metni, kategori, risk_puani FROM gmp_soru_havuzu",
        "Ayarlar_Bolumler": "SELECT id, bolum_adi, ana_departman_id, sira_no, aktif FROM ayarlar_bolumler WHERE aktif = 1 ORDER BY sira_no",
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

@st.cache_data(ttl=600) # v3.1.9: Raporlar için yüksek performanslı cache
def get_personnel_shift(personel_id, target_date=None):
    """Personelin vardiya bilgisini döndürür."""
    if target_date is None:
        target_date = datetime.now().date()

    try:
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

        sql_legacy = text("SELECT vardiya FROM personel WHERE id = :pid")
        with get_engine().connect() as conn:
            res_legacy = conn.execute(sql_legacy, {"pid": personel_id}).fetchone()
            if res_legacy and res_legacy[0]:
                return res_legacy[0]

    except Exception:
        pass

    return "GÜNDÜZ VARDİYASI"

@st.cache_data(ttl=600) # v3.1.9: Raporlar için yüksek performanslı cache
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

        sql_legacy = text("SELECT izin_gunu FROM personel WHERE id = :pid")
        with get_engine().connect() as conn:
            res_legacy = conn.execute(sql_legacy, {"pid": personel_id}).fetchone()
            if res_legacy and res_legacy[0]:
                return res_legacy[0] == today_name

    except Exception:
        pass

    return False
