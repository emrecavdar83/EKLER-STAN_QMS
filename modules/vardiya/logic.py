"""
Vardiya Modülü Logic Katmanı (v8.0.0)

Yenilikler:
  - Bit-mask izin_gunleri (S7-c)
  - plan_tipi: HAFTALIK / GUNLUK (S8-c)
  - vardiya_helper.get_aktif_vardiyalar() ile DB-driven (S10)
  - 30 satır kuralı: Tüm fonksiyonlar uyumlu (Anayasa Madde 3)
"""
import pandas as pd
from sqlalchemy import text
from logic.dynamic_sync import log_field_change, log_multiple_changes


# v8.0: Vardiya Durum FSM (Anayasa Madde 5 — Maker/Checker)
# Akış: TASLAK -> ONAY BEKLIYOR -> ONAYLANDI / REDDEDILDI
DURUM_TASLAK         = 'TASLAK'
DURUM_ONAY_BEKLIYOR  = 'ONAY BEKLIYOR'
DURUM_ONAYLANDI      = 'ONAYLANDI'
DURUM_REDDEDILDI     = 'REDDEDILDI'
GECERLI_DURUMLAR     = (DURUM_TASLAK, DURUM_ONAY_BEKLIYOR,
                        DURUM_ONAYLANDI, DURUM_REDDEDILDI)


def get_personnel_for_shift_management(engine, dept_id=None, user_rol="PERSONEL"):
    """Bölüm sorumlusu+üst amirler için aktif personel listesi (servis dahil)."""
    params = {}
    where_clause = "WHERE p.durum = 'AKTİF'"
    if dept_id and str(user_rol).upper().strip() != "ADMIN":
        if isinstance(dept_id, list):
            where_clause += " AND p.qms_departman_id IN :dept_ids"
            params["dept_ids"] = tuple(dept_id)
        else:
            where_clause += " AND p.qms_departman_id = :dept_id"
            params["dept_id"] = dept_id
    elif dept_id and isinstance(dept_id, list):
        where_clause += " AND p.qms_departman_id IN :dept_ids"
        params["dept_ids"] = tuple(dept_id)
    sql = f"""
        SELECT p.id, p.ad_soyad, p.gorev, p.bolum, p.servis_duragi,
               d.ad as departman_adi, p.izin_gunu as izin_gunleri
        FROM ayarlar_kullanicilar p
        LEFT JOIN qms_departmanlar d ON p.qms_departman_id = d.id
        {where_clause}
        ORDER BY p.ad_soyad ASC
    """
    with engine.connect() as conn:
        res = conn.execute(text(sql), params)
        return pd.DataFrame(res.fetchall(), columns=res.keys())


def get_active_shifts(engine):
    """v8.0: Aktif vardiya tipleri (DataFrame). vardiya_helper ile uyumlu."""
    sql = text(
        "SELECT tip_adi, baslangic_saati, bitis_saati FROM vardiya_tipleri "
        "WHERE aktif = 1 ORDER BY sira_no"
    )
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)


def _eski_kayit_oku(conn, pid, b, e):
    """Mevcut kaydı (varsa) okur ve dict döner."""
    sql = text("""
        SELECT id, personel_id, baslangic_tarihi, bitis_tarihi, vardiya,
               izin_gunleri, plan_tipi, aciklama, onay_durumu, onaylayan_id
        FROM personel_vardiya_programi
        WHERE personel_id = :pid AND baslangic_tarihi = :b AND bitis_tarihi = :e
        LIMIT 1
    """)
    row = conn.execute(sql, {"pid": pid, "b": b, "e": e}).fetchone()
    return dict(row._mapping) if row else {}


def _kayit_sil_ekle(conn, rec, user_id):
    """Eski kaydı sil, yenisini INSERT et. Yeni ID döner."""
    pid = rec['personel_id']
    b, e = rec['baslangic_tarihi'], rec['bitis_tarihi']
    conn.execute(text(
        "DELETE FROM personel_vardiya_programi "
        "WHERE personel_id = :pid AND baslangic_tarihi = :b AND bitis_tarihi = :e"
    ), {"pid": pid, "b": b, "e": e})
    sql = text("""
        INSERT INTO personel_vardiya_programi
        (personel_id, baslangic_tarihi, bitis_tarihi, vardiya, izin_gunleri,
         plan_tipi, aciklama, onay_durumu, onaylayan_id)
        VALUES (:pid, :b, :e, :v, :i, :pt, :a, :s, :uid)
        RETURNING id
    """)
    res = conn.execute(sql, {
        "pid": pid, "b": b, "e": e, "v": rec['vardiya'],
        "i": int(rec.get('izin_gunleri', 0) or 0),
        "pt": rec.get('plan_tipi', 'HAFTALIK'),
        "a": rec.get('aciklama', ''),
        "s": rec.get('durum', 'TASLAK'), "uid": user_id
    })
    row = res.fetchone()
    return row[0] if row else None


def save_shift_plan(engine, shift_records, user_id):
    """v8.0: Toplu vardiya kaydı. bit-mask + plan_tipi destekli."""
    try:
        with engine.begin() as conn:
            for rec in shift_records:
                old = _eski_kayit_oku(conn, rec['personel_id'],
                                      rec['baslangic_tarihi'], rec['bitis_tarihi'])
                new_id = _kayit_sil_ekle(conn, rec, user_id)
                if not new_id:
                    continue
                new_data = {
                    'vardiya': rec['vardiya'],
                    'izin_gunleri': int(rec.get('izin_gunleri', 0) or 0),
                    'plan_tipi': rec.get('plan_tipi', 'HAFTALIK'),
                    'aciklama': rec.get('aciklama', ''),
                    'onay_durumu': rec.get('durum', 'TASLAK'),
                    'onaylayan_id': user_id,
                }
                if old:
                    log_multiple_changes(conn, 'vardiya_degisim_loglari',
                                         new_id, old, new_data, user_id)
                else:
                    log_field_change(conn, 'vardiya_degisim_loglari', new_id,
                                     'onay_durumu', 'YENI',
                                     rec.get('durum', 'TASLAK'), user_id, 'INSERT')
        return True, "Kayıt Başarılı"
    except Exception as e:
        return False, str(e)


def approve_shifts(engine, record_ids, approver_id):
    """Seçili vardiya kayıtlarını onaylar. MADDE 31 audit korundu."""
    try:
        with engine.begin() as conn:
            for rid in record_ids:
                old = conn.execute(text(
                    "SELECT onay_durumu FROM personel_vardiya_programi WHERE id = :id"
                ), {"id": rid}).fetchone()
                if not old:
                    continue
                conn.execute(text("""
                    UPDATE personel_vardiya_programi
                    SET onay_durumu = 'ONAYLANDI', onaylayan_id = :aid,
                        onay_ts = CURRENT_TIMESTAMP
                    WHERE id = :id
                """), {"aid": approver_id, "id": rid})
                log_field_change(conn, 'vardiya_degisim_loglari', rid, 'onay_durumu',
                                 old[0], 'ONAYLANDI', approver_id, 'UPDATE')
        return True, "Onaylama Başarılı"
    except Exception as e:
        return False, str(e)
