"""
MADDE 2.1 — %100 Dinamiklik (Dynamic Field Synchronization)

Database şeması programı yönlendirir. Hardcoded field lists YASAK.
Tüm alanlar otomatik senkronize olur.
"""
from sqlalchemy import text, inspect
import pandas as pd

def get_table_columns(conn, table_name):
    """Veritabanındaki tüm alanları dinamik olarak getir (ANAYASA MADDE 2.1)"""
    try:
        result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 0"))
        return list(result.keys())
    except:
        return []

def sync_all_fields(conn, source_table, target_table, row_id, row_data, exclude_cols=None):
    """
    MADDE 2.1: Tüm alanları dinamik olarak senkronize et.

    Örn: sync_all_fields(conn, 'personel', 'ayarlar_kullanicilar', 2, row_data)

    Args:
        conn: Database connection
        source_table: Kaynak tablo (personel)
        target_table: Hedef tablo (ayarlar_kullanicilar)
        row_id: Satır ID
        row_data: Güncellenecek veriler (dict)
        exclude_cols: Senkronize edilmeyecek alanlar ['sifre', 'olusuturma_tarihi']
    """
    if exclude_cols is None:
        exclude_cols = ['sifre', 'olusuturma_tarihi', 'guncelleme_tarihi', 'id']

    # 1. Target table'ın hangi alanları var bul
    target_cols = get_table_columns(conn, target_table)

    if not target_cols:
        return False

    # 2. row_data'daki alanların hangisinin target table'da var olduğunu kontrol et
    sync_fields = {}
    for col, val in row_data.items():
        if col in target_cols and col not in exclude_cols:
            sync_fields[col] = val

    if not sync_fields:
        return False

    # 3. Dinamik UPDATE cümlesi oluştur (hardcoded field list YOK!)
    set_clause = ", ".join([f"{col}=:{col}" for col in sync_fields.keys()])
    sql_text = text(f"UPDATE {target_table} SET {set_clause} WHERE id=:row_id")

    # 4. Parametreleri hazırla
    params = sync_fields.copy()
    params['row_id'] = row_id

    # 5. Senkronize et
    try:
        conn.execute(sql_text, params)
        return True
    except Exception as e:
        print(f"[SYNC ERROR] {source_table} -> {target_table}: {e}")
        return False

def sync_personnel_to_users(conn, personnel_id, personnel_data):
    """
    Kolaylık: Personel → Kullanıcı senkronizasyonu

    MADDE 2.1 UYUMLU: Tüm alanlar otomatik senkronize olur.
    Yeni alan eklenirse → Kod değişikliği YOK, otomatik çalışır.

    Args:
        conn: Database connection
        personnel_id: Personel ID
        personnel_data: Personel satırı (dict veya row)
    """
    exclude = ['sifre', 'kullanici_adi', 'olusuturma_tarihi']

    # Dict'e çevir (eğer row object ise)
    if hasattr(personnel_data, 'to_dict'):
        data_dict = personnel_data.to_dict()
    elif isinstance(personnel_data, dict):
        data_dict = personnel_data
    else:
        return False

    return sync_all_fields(conn, 'personel', 'ayarlar_kullanicilar',
                          personnel_id, data_dict, exclude)
