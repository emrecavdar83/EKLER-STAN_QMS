"""
EKLERİSTAN QDMS — Yayım Yönetim Modülü
Durum makinesi ve yayım geçmişi
"""
from sqlalchemy import text
from modules.qdms.belge_kayit import belge_getir, belge_durum_guncelle

GECERLI_DURUM_GECISLERI = {
    'taslak': ['incelemede'],
    'incelemede': ['aktif', 'taslak'],
    'aktif': ['arsiv'],
    'arsiv': []
}

def belge_yayimla(db_conn, belge_kodu, yayimlayan_id, notu=None) -> dict:
    """incelemede -> aktif geçişi yapar ve yayım logu atar."""
    belge = belge_getir(db_conn, belge_kodu)
    if not belge:
        return {"basarili": False, "hata": "Belge bulunamadı"}
    
    if belge['durum'] != 'incelemede':
        return {"basarili": False, "hata": f"Yayım için belge 'incelemede' olmalıdır. Mevcut durum: {belge['durum']}"}
    
    try:
        # Eğer db_conn zaten bir connection ise doğrudan kullan, Engine ise begin aç
        if hasattr(db_conn, 'begin') and not hasattr(db_conn, 'execute'):
            with db_conn.begin() as conn:
                belge_durum_guncelle(conn, belge_kodu, 'aktif', yayimlayan_id)
                _yayim_log_ekle(conn, belge_kodu, belge['aktif_rev'], yayimlayan_id, notu)
        else:
            belge_durum_guncelle(db_conn, belge_kodu, 'aktif', yayimlayan_id)
            _yayim_log_ekle(db_conn, belge_kodu, belge['aktif_rev'], yayimlayan_id, notu)
            if hasattr(db_conn, 'commit'): db_conn.commit()
        return {"basarili": True}
    except Exception as e:
        return {"basarili": False, "hata": str(e)}

def belge_iptal_et(db_conn, belge_kodu, iptal_eden_id, onay_verildi=False) -> dict:
    """T2 İşlem: aktif -> arsiv geçişi yapar."""
    if not onay_verildi:
        return {"basarili": False, "hata": "İptal işlemi için onay verilmelidir."}
    
    return belge_durum_guncelle(db_conn, belge_kodu, 'arsiv', iptal_eden_id)

def _yayim_log_ekle(db_conn, belge_kodu, rev_no, yayimlayan_id, notu):
    sql = text("""
        INSERT INTO qdms_yayim (belge_kodu, rev_no, yayimlayan_id, yayim_notu)
        VALUES (:kod, :rev, :yid, :not)
    """)
    if hasattr(db_conn, 'execute'):
        db_conn.execute(sql, {"kod": belge_kodu, "rev": rev_no, "yid": yayimlayan_id, "not": notu})
    else:
        with db_conn.connect() as conn:
            conn.execute(sql, {"kod": belge_kodu, "rev": rev_no, "yid": yayimlayan_id, "not": notu})
            if hasattr(conn, 'commit'): conn.commit()

def aktif_belgeler_listele(db_conn):
    sql = text("SELECT * FROM qdms_belgeler WHERE durum = 'aktif'")
    if hasattr(db_conn, 'execute'):
        res = db_conn.execute(sql).fetchall()
    else:
        with db_conn.connect() as conn:
            res = conn.execute(sql).fetchall()
    return [dict(r._mapping) for r in res]
