import uuid
from sqlalchemy import text
from modules.qdms.belge_kayit import _exec_commit

def talimat_olustur(db_conn, talimat_kodu, talimat_adi,
                     talimat_tipi, adimlar, belge_kodu=None, ekipman_id=None, departman=None):
    """
    Yeni bir talimat (SOP) oluşturur ve QR token üretir.
    adimlar: list of dict [{"sira":1, "baslik":"...", "aciklama":"..."}]
    """
    import json
    qr_token = str(uuid.uuid4())
    adimlar_json = json.dumps(adimlar, ensure_ascii=False)
    
    sql = text("""
        INSERT INTO qdms_talimatlar (talimat_kodu, belge_kodu, talimat_adi, talimat_tipi, ekipman_id, departman, adimlar_json, qr_token)
        VALUES (:tk, :bk, :ta, :tt, :eid, :dep, :aj, :qt)
    """)
    
    params = {
        "tk": talimat_kodu, "bk": belge_kodu, "ta": talimat_adi, 
        "tt": talimat_tipi, "eid": ekipman_id, "dep": departman, 
        "aj": adimlar_json, "qt": qr_token
    }
    
    try:
        _exec_commit(db_conn, sql, params)
        return {"basarili": True, "talimat_kodu": talimat_kodu, "qr_token": qr_token}
    except Exception as e:
        return {"basarili": False, "hata": str(e)}

def talimat_guncelle(db_conn, talimat_kodu, adimlar):
    """Talimat adımlarını günceller."""
    import json
    adimlar_json = json.dumps(adimlar, ensure_ascii=False)
    sql = text("UPDATE qdms_talimatlar SET adimlar_json = :aj WHERE talimat_kodu = :tk")
    try:
        if hasattr(db_conn, 'begin'):
            with db_conn.begin() as conn:
                conn.execute(sql, {"aj": adimlar_json, "tk": talimat_kodu})
        else:
            db_conn.execute(sql, {"aj": adimlar_json, "tk": talimat_kodu})
        return {"basarili": True}
    except Exception as e:
        return {"basarili": False, "hata": str(e)}

def talimat_qr_ile_getir(db_conn, qr_token):
    sql = text("SELECT id, talimat_kodu, belge_kodu, talimat_adi, talimat_tipi, ekipman_id, departman, adimlar_json, gorsel_url, qr_token, aktif, rev_no, olusturma_tarihi FROM qdms_talimatlar WHERE qr_token = :qt AND aktif = 1")
    try:
        if hasattr(db_conn, 'execute'):
            res = db_conn.execute(sql, {"qt": qr_token}).fetchone()
        else:
            with db_conn.connect() as conn:
                res = conn.execute(sql, {"qt": qr_token}).fetchone()
        if res: return dict(res._mapping)
    except: pass
    return None

def talimat_getir_by_kod(db_conn, talimat_kodu):
    """Talimatı koduyla getirir."""
    sql = text("SELECT id, talimat_kodu, belge_kodu, talimat_adi, talimat_tipi, ekipman_id, departman, adimlar_json, gorsel_url, qr_token, aktif, rev_no, olusturma_tarihi FROM qdms_talimatlar WHERE talimat_kodu = :tk AND aktif = 1")
    try:
        if hasattr(db_conn, 'execute'):
            res = db_conn.execute(sql, {"tk": talimat_kodu}).fetchone()
        else:
            with db_conn.connect() as conn:
                res = conn.execute(sql, {"tk": talimat_kodu}).fetchone()
        if res: return dict(res._mapping)
    except: pass
    return None

def okuma_onay_kaydet(db_conn, belge_kodu, rev_no, personel_id, onay_tipi='manuel'):
    """Personelin dokümanı/talimatı okuduğunu belgeler."""
    sql = text("""
        INSERT INTO qdms_okuma_onay (belge_kodu, rev_no, personel_id, onay_tipi, okuma_tarihi)
        VALUES (:bk, :rev, :pid, :oti, CURRENT_TIMESTAMP)
    """)
    try:
        _exec_commit(db_conn, sql, {"bk": belge_kodu, "rev": rev_no, "pid": personel_id, "oti": onay_tipi})
        return {"basarili": True}
    except Exception as e:
        return {"basarili": False, "hata": str(e)}

def okunmayan_talimatlar(db_conn, personel_id):
    """Personelin henüz onaylamadığı aktif talimatları listeler."""
    sql = text("""
        SELECT t.* FROM qdms_talimatlar t
        WHERE t.aktif = 1 AND NOT EXISTS (
            SELECT 1 FROM qdms_okuma_onay o 
            WHERE o.belge_kodu = t.talimat_kodu AND o.personel_id = :pid
        )
    """)
    try:
        if hasattr(db_conn, 'execute'):
            res = db_conn.execute(sql, {"pid": personel_id}).fetchall()
        else:
            with db_conn.connect() as conn:
                res = conn.execute(sql, {"pid": personel_id}).fetchall()
        return [dict(r._mapping) for r in res]
    except: return []
