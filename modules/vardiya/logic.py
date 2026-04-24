import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta
from logic.dynamic_sync import log_field_change, log_multiple_changes

def get_personnel_for_shift_management(engine, dept_id=None, user_rol="PERSONEL"):
    """
    Bölüm sorumlusu veya üst amirler için ayarlar_kullanicilar listesini, 
    servis güzergahları ve mevcut vardiya statüleri ile birlikte getirir.
    v8.3.1: Hiyerarşik Bölüm Desteği & SQLAlchemy 2.0 (Manual Fetch)
    """
    params = {}
    where_clause = "WHERE p.durum = 'AKTİF'"
    
    # v6.3.3: Department Filter Logic (Multiple ID support for Hierarchy)
    if dept_id and str(user_rol).upper().strip() != "ADMIN":
        if isinstance(dept_id, list):
            where_clause += " AND p.qms_departman_id IN :dept_ids"
            params["dept_ids"] = tuple(dept_id)
        else:
            where_clause += " AND p.qms_departman_id = :dept_id"
            params["dept_id"] = dept_id

    # v6.8.9: Targeted Source - Shift management now covers ALL personnel, not just users
    sql = f"""
        SELECT 
            p.id, p.ad_soyad, p.gorev, p.bolum, p.servis_duragi,
            d.ad as departman_adi
        FROM personel p
        LEFT JOIN qms_departmanlar d ON p.qms_departman_id = d.id
        {where_clause}
        ORDER BY p.ad_soyad ASC
    """
    
    with engine.connect() as conn:
        res = conn.execute(text(sql), params)
        return pd.DataFrame(res.fetchall(), columns=res.keys())

def get_active_shifts(engine):
    """Sistemde tanımlı ve aktif vardiya tiplerini (saatleriyle) döner."""
    sql = text("SELECT tip_adi, baslangic_saati, bitis_saati FROM vardiya_tipleri WHERE aktif = 1 ORDER BY sira_no")
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)

def save_shift_plan(engine, shift_records, user_id):
    """
    Toplu vardiya kayıtlarını 'TASLAK' veya 'ONAY BEKLIYOR' statüsünde kaydeder.
    MADDE 31: Tüm değişiklikler audit trail'e kaydedilir.
    """
    try:
        with engine.begin() as conn:
            for rec in shift_records:
                pid = rec['personel_id']
                b = rec['baslangic_tarihi']
                e = rec['bitis_tarihi']

                # Eski kaydı al (eğer varsa)
                old_rec = conn.execute(text("""
                    SELECT id, personel_id, baslangic_tarihi, bitis_tarihi, vardiya, izin_gunleri, aciklama, olusturma_tarihi, onay_durumu, onaylayan_id, onay_ts FROM personel_vardiya_programi
                    WHERE personel_id = :pid AND baslangic_tarihi = :b AND bitis_tarihi = :e
                    LIMIT 1
                """), {"pid": pid, "b": b, "e": e}).fetchone()

                old_data = dict(old_rec) if old_rec else {}

                # Eski kaydı sil
                conn.execute(text("""
                    DELETE FROM personel_vardiya_programi
                    WHERE personel_id = :pid AND baslangic_tarihi = :b AND bitis_tarihi = :e
                """), {"pid": pid, "b": b, "e": e})

                # Yeni kaydı ekle
                sql = text("""
                    INSERT INTO personel_vardiya_programi
                    (personel_id, baslangic_tarihi, bitis_tarihi, vardiya, izin_gunleri, aciklama, onay_durumu, onaylayan_id)
                    VALUES (:pid, :b, :e, :v, :i, :a, :s, :uid)
                    RETURNING id
                """)
                res = conn.execute(sql, {
                    "pid": pid, "b": b, "e": e,
                    "v": rec['vardiya'], "i": rec.get('izin_gunleri', ''),
                    "a": rec.get('aciklama', ''),
                    "s": rec.get('durum', 'TASLAK'), "uid": user_id
                })

                new_id = res.fetchone()[0]

                # MADDE 31: Yapılan değişiklikleri logla
                new_data = {
                    'vardiya': rec['vardiya'],
                    'izin_gunleri': rec.get('izin_gunleri', ''),
                    'aciklama': rec.get('aciklama', ''),
                    'onay_durumu': rec.get('durum', 'TASLAK'),
                    'onaylayan_id': user_id
                }

                if old_data:
                    # Güncelleme — değişiklikleri logla
                    log_multiple_changes(conn, 'vardiya_degisim_loglari', new_id, old_data, new_data, user_id)
                else:
                    # INSERT — yeni kayıt logla
                    log_field_change(conn, 'vardiya_degisim_loglari', new_id, 'onay_durumu',
                                   'YENI', rec.get('durum', 'TASLAK'), user_id, 'INSERT')

        return True, "Kayıt Başarılı"
    except Exception as e:
        return False, str(e)

def approve_shifts(engine, record_ids, approver_id):
    """Seçili vardiya kayıtlarını onaylar. MADDE 31: Onay işlemi audit trail'e kaydedilir."""
    try:
        with engine.begin() as conn:
            # Her kayıt için eski durumu al ve logla
            for rid in record_ids:
                old = conn.execute(text(
                    "SELECT onay_durumu FROM personel_vardiya_programi WHERE id = :id"
                ), {"id": rid}).fetchone()

                if old:
                    old_status = old[0]
                    # Onayı güncelle
                    conn.execute(text("""
                        UPDATE personel_vardiya_programi
                        SET onay_durumu = 'ONAYLANDI', onaylayan_id = :aid, onay_ts = CURRENT_TIMESTAMP
                        WHERE id = :id
                    """), {"aid": approver_id, "id": rid})

                    # MADDE 31: Değişikliği logla
                    log_field_change(conn, 'vardiya_degisim_loglari', rid, 'onay_durumu',
                                   old_status, 'ONAYLANDI', approver_id, 'UPDATE')

        return True, "Onaylama Başarılı"
    except Exception as e:
        return False, str(e)
