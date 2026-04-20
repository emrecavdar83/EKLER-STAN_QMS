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
        # PostgreSQL metadata yöntemi (daha güvenli)
        from sqlalchemy import MetaData, Table
        metadata = MetaData()
        table = Table(table_name, metadata, autoload_with=conn)
        return [col.name for col in table.columns]
    except:
        # Fallback: SELECT * LIMIT 0
        try:
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT 0"))
            return list(result.keys())
        except Exception as e:
            print(f"[SYNC ERROR] get_table_columns({table_name}): {e}")
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

def log_field_change(conn, audit_table, source_id, field_name, old_value, new_value, user_id, op_type='UPDATE'):
    """
    MADDE 31 — Detaylı Değişim Loglama (Field-Level Audit Trail)

    Alan seviyesinde her değişikliği zaman damgası ile kaydeder.

    Args:
        conn: Database connection
        audit_table: Audit table ismi (örn: 'vardiya_degisim_loglari')
        source_id: Muhasebesi için FK alan ismi (örn: 'vardiya_id')
        field_name: Değişen alan adı
        old_value: Eski değer
        new_value: Yeni değer
        user_id: Değişikliği yapan kullanıcı ID
        op_type: İşlem tipi (UPDATE/INSERT/DELETE)
    """
    try:
        # source_id parametresinin ismine göre SQL ID alanını belirle
        # Örn: audit_table='vardiya_degisim_loglari' → source_id_col='vardiya_id'
        source_id_col = audit_table.replace('_degisim_loglari', '_id').replace('_detay', '_id')

        sql = text(f"""
            INSERT INTO {audit_table} ({source_id_col}, alan_adi, eski_deger, yeni_deger, degistiren_kullanici_id, islem_tipi)
            VALUES (:{source_id_col}, :alan_adi, :eski_deger, :yeni_deger, :user_id, :op_type)
        """)

        params = {
            source_id_col: source_id,
            'alan_adi': field_name,
            'eski_deger': str(old_value) if old_value is not None else None,
            'yeni_deger': str(new_value) if new_value is not None else None,
            'user_id': user_id,
            'op_type': op_type
        }

        conn.execute(sql, params)
        return True
    except Exception as e:
        print(f"[AUDIT LOG ERROR] {audit_table}: {e}")
        return False

def log_multiple_changes(conn, audit_table, source_id, old_row, new_row, user_id, exclude_fields=None):
    """
    MADDE 31 — Toplu Değişim Loglama

    İki satır arasındaki tüm farkları bulur ve loglar.

    Args:
        conn: Database connection
        audit_table: Audit table ismi
        source_id: Kaynağın ID değeri
        old_row: Eski satır (dict)
        new_row: Yeni satır (dict)
        user_id: Değişikliği yapan kullanıcı ID
        exclude_fields: Loglanmayacak alanlar
    """
    if exclude_fields is None:
        exclude_fields = ['id', 'olusuturma_tarihi', 'degisim_tarihi', 'olusturulma_tarihi']

    if old_row is None:
        old_row = {}

    # Tüm alanları al
    all_fields = set(list(old_row.keys()) + list(new_row.keys()))

    success_count = 0
    for field in all_fields:
        if field in exclude_fields:
            continue

        old_val = old_row.get(field)
        new_val = new_row.get(field)

        # Eğer değişmişse logla
        if old_val != new_val:
            if log_field_change(conn, audit_table, source_id, field, old_val, new_val, user_id):
                success_count += 1

    return success_count > 0
