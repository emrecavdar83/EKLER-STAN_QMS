import pandas as pd
from sqlalchemy import text
from datetime import datetime, timedelta

def get_personnel_for_shift_management(engine, dept_id=None, user_rol="PERSONEL"):
    """
    Bölüm sorumlusu veya üst amirler için personel listesini, 
    servis güzergahları ve mevcut vardiya statüleri ile birlikte getirir.
    """
    params = {}
    where_clause = "WHERE p.durum = 'AKTİF'"
    
    if dept_id and user_rol != "ADMIN":
        where_clause += " AND p.departman_id = :dept_id"
        params["dept_id"] = dept_id

    sql = text(f"""
        SELECT 
            p.id, p.ad_soyad, p.gorev, p.bolum, p.servis_duragi,
            d.bolum_adi as departman_adi
        FROM personel p
        LEFT JOIN ayarlar_bolumler d ON p.departman_id = d.id
        {where_clause}
        ORDER BY p.ad_soyad ASC
    """)
    
    with engine.connect() as conn:
        return pd.read_sql(sql, conn, params=params)

def get_active_shifts(engine):
    """Sistemde tanımlı ve aktif vardiya tiplerini (saatleriyle) döner."""
    sql = text("SELECT tip_adi, baslangic_saati, bitis_saati FROM vardiya_tipleri WHERE aktif = 1 ORDER BY sira_no")
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)

def save_shift_plan(engine, shift_records, user_id):
    """
    Toplu vardiya kayıtlarını 'TASLAK' veya 'ONAY BEKLIYOR' statüsünde kaydeder.
    """
    try:
        with engine.begin() as conn:
            for rec in shift_records:
                # v5.8.5: Madde 7 - Çakışma kontrolü sonrası UPSERT
                # Önce o tarihteki kaydı temizle (Zarar Vermeme - Madde 23)
                conn.execute(text("""
                    DELETE FROM personel_vardiya_programi 
                    WHERE personel_id = :pid AND baslangic_tarihi = :b AND bitis_tarihi = :e
                """), {"pid": rec['personel_id'], "b": rec['baslangic_tarihi'], "e": rec['bitis_tarihi']})
                
                # Yeni kaydı ekle
                sql = text("""
                    INSERT INTO personel_vardiya_programi 
                    (personel_id, baslangic_tarihi, bitis_tarihi, vardiya, izin_gunleri, aciklama, onay_durumu, onaylayan_id)
                    VALUES (:pid, :b, :e, :v, :i, :a, :s, :uid)
                """)
                conn.execute(sql, {
                    "pid": rec['personel_id'], "b": rec['baslangic_tarihi'], "e": rec['bitis_tarihi'],
                    "v": rec['vardiya'], "i": rec.get('izin_gunleri', ''), "a": rec.get('aciklama', ''),
                    "s": rec.get('durum', 'TASLAK'), "uid": user_id
                })
        return True, "Kayıt Başarılı"
    except Exception as e:
        return False, str(e)

def approve_shifts(engine, record_ids, approver_id):
    """Seçili vardiya kayıtlarını onaylar."""
    try:
        with engine.begin() as conn:
            sql = text("""
                UPDATE personel_vardiya_programi 
                SET onay_durumu = 'ONAYLANDI', onaylayan_id = :aid, onay_ts = CURRENT_TIMESTAMP
                WHERE id IN :ids
            """)
            conn.execute(sql, {"aid": approver_id, "ids": tuple(record_ids)})
        return True, "Onaylama Başarılı"
    except Exception as e:
        return False, str(e)
