"""
Settings Logic Module
=====================
Bu modül, app.py içindeki Ayarlar (Settings) modülünden çıkarılan
mantıksal fonksiyonları içerir. Amaç, kodun daha yönetilebilir ve
test edilebilir hale getirilmesidir.

Modül İçeriği:
-------------
- Personel yönetimi (kaydet, sil, hiyerarşi eşleme)
- Kullanıcı yönetimi (kullanıcı adı önerisi, şifre güncellemeleri)
- Ürün ve Parametre yönetimi
- Bölüm ve Lokasyon hiyerarşisi yönetimi
- Proses atama mantığı
- Temizlik master plan işlemleri
- GMP Soru Bankası işlemleri
"""

import pandas as pd
import re
from typing import List, Dict, Optional, Tuple
from sqlalchemy import text


# ============================================================================
# PERSONEL YÖNETİMİ FONKSİYONLARI
# ============================================================================

def get_personnel_hierarchy(conn) -> pd.DataFrame:
    """
    Personel hiyerarşisini veritabanından çeker.

    Args:
        conn: SQLAlchemy bağlantı nesnesi

    Returns:
        pd.DataFrame: Personel hiyerarşi verileri
    """
    query = """
        SELECT
            p.id,
            p.ad,
            p.bolum_id,
            b.bolum_adi,
            p.ust_seviye,
            p.pozisyon,
            p.rol
        FROM personel p
        LEFT JOIN tanim_bolumler b ON p.bolum_id = b.id
        WHERE p.aktif = 1
        ORDER BY p.ust_seviye, p.bolum_id
    """
    return pd.read_sql(text(query), conn)


def suggest_username(full_name: str) -> str:
    """
    Personelin tam adından kullanıcı adı önerisi oluşturur.

    Kurallar:
    - Ad ve soyadın ilk harfleri küçük harf
    - Türkçe karakterler İngilizce karşılıklarına çevrilir
    - Boşluklar kaldırılır

    Args:
        full_name: Personelin tam adı (örn: "Emre ÇAVDAR")

    Returns:
        str: Önerilen kullanıcı adı (örn: "ecavdar")

    Örnek:
        >>> suggest_username("Emre ÇAVDAR")
        'ecavdar'
        >>> suggest_username("Mehmet Ali YILMAZ")
        'mayilmaz'
    """
    # Türkçe karakterleri İngilizce karşılıklarına çevir
    tr_chars = "ğüşıöçĞÜŞİÖÇ"
    en_chars = "gusiocGUSIOC"
    trans_table = str.maketrans(tr_chars, en_chars)

    # Temizle ve normalize et
    name = full_name.strip().translate(trans_table).lower()

    # Birden fazla boşluk varsa tek boşluğa indir
    name = re.sub(r'\s+', ' ', name)

    parts = name.split()
    if len(parts) >= 2:
        # İlk ad + Soyad formatı
        first_initial = parts[0][0] if parts[0] else ''
        last_name = parts[-1] if parts[-1] else ''
        return f"{first_initial}{last_name}"
    elif len(parts) == 1:
        # Sadece tek isim varsa olduğu gibi al
        return parts[0]
    else:
        return "kullanici"


def assign_role_by_hierarchy(hierarchy_level: int) -> str:
    """
    Personelin hiyerarşik seviyesine göre otomatik rol atar.

    Rules:
    - Seviye 1: Admin (Üst yönetim)
    - Seviye 2: Manager (Orta yönetim)
    - Seviye 3+: User (Personel)

    Args:
        hierarchy_level: Personelin hiyerarşik seviyesi

    Returns:
        str: Atanacak rol adı
    """
    if hierarchy_level == 1:
        return "Admin"
    elif hierarchy_level == 2:
        return "Manager"
    else:
        return "User"


def clean_department_ids(df: pd.DataFrame, id_column: str = 'bolum_id') -> pd.DataFrame:
    """
    DataFrame'deki bölüm ID'lerini temizler ve integer'a çevirir.

    Bu fonksiyon, st.data_editor'den gelen karışık formattaki ID'leri
    (örn: "5 - Üretim Müdürlüğü") temizleyip sadece sayısal kısmı alır.

    Args:
        df: Temizlenecek DataFrame
        id_column: ID sütununun adı

    Returns:
        pd.DataFrame: Temizlenmiş DataFrame
    """
    df = df.copy()

    if id_column in df.columns:
        def extract_id(value):
            if pd.isna(value):
                return None
            # String ise ilk sayısal kısmı al
            if isinstance(value, str):
                match = re.search(r'^\d+', value.strip())
                if match:
                    return int(match.group())
            # Sayı ise direkt al
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return None

        df[id_column] = df[id_column].apply(extract_id)

    return df


def validate_personnel_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Personel verilerini kaydedilmeden önce doğrular.

    Kontroller:
    - İsim tekrarı var mı?
    - Gerekli alanlar dolu mu?
    - Bölüm ID'leri geçerli mi?

    Args:
        df: Doğrulanacak personel DataFrame'i

    Returns:
        Tuple[bool, List[str]]: (Geçerli mi?, Hata mesajları listesi)
    """
    errors = []

    # İsim tekrarı kontrolü
    if 'ad' in df.columns:
        duplicates = df[df.duplicated('ad', keep=False)]['ad'].unique()
        if len(duplicates) > 0:
            errors.append(f"Tekrar eden isimler: {', '.join(duplicates)}")

    # Boş isim kontrolü
    if 'ad' in df.columns:
        empty_names = df[df['ad'].isna() | (df['ad'].str.strip() == '')]
        if len(empty_names) > 0:
            errors.append(f"{len(empty_names)} adet boş isim bulundu.")

    # Geçersiz bölüm ID kontrolü
    if 'bolum_id' in df.columns:
        invalid_depts = df[df['bolum_id'].isna()]
        if len(invalid_depts) > 0:
            errors.append(f"{len(invalid_depts)} adet personelin bölümü atanmamış.")

    return (len(errors) == 0, errors)


# ============================================================================
# BÖLÜM VE LOKASYON HİYERARŞİSİ FONKSİYONLARI
# ============================================================================

def get_department_tree(conn, parent_id: Optional[int] = None) -> List[Dict]:
    """
    Bölüm hiyerarşisini ağaç yapısında getirir (recursive).

    Args:
        conn: SQLAlchemy bağlantı nesnesi
        parent_id: Üst bölüm ID'si (None ise kök bölümler)

    Returns:
        List[Dict]: Hiyerarşik bölüm listesi
    """
    if parent_id is None:
        query = """
            SELECT id, bolum_adi, ustbirim_id, sira_no, tur
            FROM tanim_bolumler
            WHERE ustbirim_id IS NULL
            ORDER BY sira_no, bolum_adi
        """
    else:
        query = f"""
            SELECT id, bolum_adi, ustbirim_id, sira_no, tur
            FROM tanim_bolumler
            WHERE ustbirim_id = {parent_id}
            ORDER BY sira_no, bolum_adi
        """

    departments = pd.read_sql(text(query), conn).to_dict('records')

    # Her bölüm için çocuklarını recursive çek
    for dept in departments:
        dept['children'] = get_department_tree(conn, dept['id'])

    return departments


def flatten_department_hierarchy(tree: List[Dict], level: int = 0, prefix: str = "") -> List[Dict]:
    """
    Ağaç yapısındaki bölüm hiyerarşisini düz listeye çevirir.

    Args:
        tree: get_department_tree'den dönen ağaç yapısı
        level: Şu anki seviye (indent için)
        prefix: Görüntüleme için prefix

    Returns:
        List[Dict]: Düzleştirilmiş bölüm listesi
    """
    flattened = []

    for dept in tree:
        indent = "  " * level
        display_name = f"{indent}{prefix}{dept['bolum_adi']}"

        flattened.append({
            'id': dept['id'],
            'name': dept['bolum_adi'],
            'display_name': display_name,
            'level': level,
            'parent_id': dept.get('ustbirim_id')
        })

        # Çocukları ekle
        if dept.get('children'):
            flattened.extend(
                flatten_department_hierarchy(dept['children'], level + 1, "└─ ")
            )

    return flattened


# ============================================================================
# GMP SORU BANKASI FONKSİYONLARI
# ============================================================================

def find_excel_column(df: pd.DataFrame, keywords: List[str]) -> Optional[str]:
    """
    Excel'deki sütun başlıklarını anahtar kelimeler ile eşleştirir.

    Args:
        df: Excel'den okunan DataFrame
        keywords: Aranacak anahtar kelimeler listesi

    Returns:
        Optional[str]: Bulunan sütun adı veya None
    """
    # Sütun başlıklarını normalize et
    cols = {str(c).upper().strip(): c for c in df.columns}

    for col_upper, original_name in cols.items():
        for keyword in keywords:
            if keyword.upper() in col_upper:
                return original_name

    return None


def parse_location_ids(location_ids_str: Optional[str]) -> List[int]:
    """
    Lokasyon ID string'ini liste formatına çevirir.

    Args:
        location_ids_str: Virgülle ayrılmış ID'ler (örn: "1,2,3")

    Returns:
        List[int]: ID listesi

    Örnek:
        >>> parse_location_ids("13,19,25")
        [13, 19, 25]
        >>> parse_location_ids(None)
        []
    """
    if not location_ids_str or pd.isna(location_ids_str):
        return []

    try:
        return [int(x.strip()) for x in str(location_ids_str).split(',') if x.strip()]
    except (ValueError, AttributeError):
        return []


def format_location_ids(location_ids: List[int]) -> str:
    """
    Lokasyon ID listesini veritabanı formatına çevirir.

    Args:
        location_ids: ID listesi

    Returns:
        str: Virgülle ayrılmış ID string'i

    Örnek:
        >>> format_location_ids([13, 19, 25])
        '13,19,25'
    """
    if not location_ids:
        return ""

    return ','.join(map(str, location_ids))


# ============================================================================
# VERİ BÜTÜNLÜĞÜ ve TRANSACTION YÖNETİMİ
# ============================================================================

def execute_with_transaction(engine, operations: List[Tuple[str, Dict]]) -> Tuple[bool, Optional[str]]:
    """
    Birden fazla SQL işlemini atomic transaction içinde çalıştırır.

    Args:
        engine: SQLAlchemy engine
        operations: (SQL sorgusu, parametreler) tuple'larının listesi

    Returns:
        Tuple[bool, Optional[str]]: (Başarılı mı?, Hata mesajı)

    Örnek:
        operations = [
            ("DELETE FROM personel WHERE id = :id", {"id": 5}),
            ("INSERT INTO log (action) VALUES (:action)", {"action": "delete"})
        ]
        success, error = execute_with_transaction(engine, operations)
    """
    try:
        with engine.begin() as conn:
            for sql, params in operations:
                conn.execute(text(sql), params)
        return (True, None)
    except Exception as e:
        return (False, str(e))
