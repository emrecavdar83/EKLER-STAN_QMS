"""
EKLERİSTAN QDMS — Revizyon Modülü
Revizyon döngüsü ve geçmişi yönetimi
"""
from sqlalchemy import text

def revizyon_baslat(db_conn, belge_kodu, degisiklik_notu, degistiren_id, onay_verildi=False) -> dict:
    """
    T2 İşlem: Yeni revizyon başlatır, durumu taslağa çeker.
    """
    if not onay_verildi:
        return {"basarili": False, "hata": "T2 İşlem uyarısı: Revizyon başlatmak için onay verilmelidir."}
    
    if not degisiklik_notu or len(degisiklik_notu.strip()) < 5:
        return {"basarili": False, "hata": "Geçerli bir revizyon notu girilmelidir."}

    # Mevcut revizyonu al
    eski_rev = aktif_rev_getir(db_conn, belge_kodu)
    yeni_rev = eski_rev + 1
    
    try:
        sql_update = text("""
            UPDATE qdms_belgeler 
            SET aktif_rev = :yeni_rev, durum = 'taslak', guncelleme_tarihi = CURRENT_TIMESTAMP
            WHERE belge_kodu = :kod
        """)
        
        # Atomik işlem
        if hasattr(db_conn, 'begin'):
            with db_conn.begin() as conn:
                conn.execute(sql_update, {"yeni_rev": yeni_rev, "kod": belge_kodu})
                revizyon_log_ekle(conn, belge_kodu, eski_rev, yeni_rev, degisiklik_notu, degistiren_id)
        else:
            db_conn.execute(sql_update, {"yeni_rev": yeni_rev, "kod": belge_kodu})
            revizyon_log_ekle(db_conn, belge_kodu, eski_rev, yeni_rev, degisiklik_notu, degistiren_id)
            
        return {"basarili": True, "yeni_rev": yeni_rev}
    except Exception as e:
        return {"basarili": False, "hata": str(e)}

def revizyon_log_ekle(db_conn, belge_kodu, eski_rev, yeni_rev, degisiklik_notu, degistiren_id):
    sql = text("""
        INSERT INTO qdms_revizyon_log (belge_kodu, eski_rev, yeni_rev, degisiklik_notu, degistiren_id)
        VALUES (:kod, :erev, :yrev, :not, :did)
    """)
    db_conn.execute(sql, {"kod": belge_kodu, "erev": eski_rev, "yrev": yeni_rev, "not": degisiklik_notu, "did": degistiren_id})

def revizyon_gecmisi_getir(db_conn, belge_kodu):
    sql = text("SELECT * FROM qdms_revizyon_log WHERE belge_kodu = :kod ORDER BY degisiklik_tarihi DESC")
    if hasattr(db_conn, 'connect'):
        with db_conn.connect() as conn:
            res = conn.execute(sql, {"kod": belge_kodu}).fetchall()
    else:
        res = db_conn.execute(sql, {"kod": belge_kodu}).fetchall()
    return [dict(r._mapping) for r in res]

def aktif_rev_getir(db_conn, belge_kodu):
    sql = text("SELECT aktif_rev FROM qdms_belgeler WHERE belge_kodu = :kod")
    if hasattr(db_conn, 'connect'):
        with db_conn.connect() as conn:
            res = conn.execute(sql, {"kod": belge_kodu}).fetchone()
    else:
        res = db_conn.execute(sql, {"kod": belge_kodu}).fetchone()
    return res[0] if res else 1
