"""
EKLERİSTAN QDMS — Belge Kayıt Modülü
Belge CRUD, durum yönetimi, kod formatı doğrulama
"""
import re
from sqlalchemy import text, Engine

def belge_kod_dogrula(belge_kodu: str) -> bool:
    """Format: EKL-[TIP]-[3HANE]"""
    pattern = r"^EKL-(SO|TL|PR|KYS|UR|HACCP)-\d{3}$"
    return bool(re.match(pattern, belge_kodu))

def _exec_commit(db_conn, sql, params):
    """SQLAlchemy 2.0 uyumlu güvenli execute + commit."""
    # 1. Engine gelirse (Yüksek seviye çağrı): begin() ile transaction açar ve oto-commit yapar.
    if hasattr(db_conn, 'begin') and not hasattr(db_conn, 'execute'):
        with db_conn.begin() as conn:
            return conn.execute(sql, params)
    
    # 2. Connection gelirse (Düşük seviye/nested çağrı): 
    # Zaten bir transaction içinde olduğu varsayılır (Anayasa 13th Man: Caller manages transaction).
    return db_conn.execute(sql, params)

def belge_olustur(db_conn, belge_kodu: str, belge_adi: str,
                  belge_tipi: str, alt_kategori: str,
                  aciklama: str, olusturan_id: int) -> dict:
    if not belge_kod_dogrula(belge_kodu):
        return {"basarili": False, "hata": "Belge kodu formatı geçersiz (ör: EKL-SO-001)"}
    
    sql = text("""
        INSERT INTO qdms_belgeler (belge_kodu, belge_adi, belge_tipi, alt_kategori, aciklama, olusturan_id)
        VALUES (:kod, :ad, :tip, :kat, :aciklama, :oid)
    """)
    try:
        _exec_commit(db_conn, sql, {"kod": belge_kodu, "ad": belge_adi, "tip": belge_tipi, "kat": alt_kategori, "aciklama": aciklama, "oid": olusturan_id})
        return {"basarili": True, "belge_kodu": belge_kodu}
    except Exception as e:
        return {"basarili": False, "hata": str(e)}

def belge_durum_guncelle(db_conn, belge_kodu: str, yeni_durum: str, guncelleyen_id: int) -> dict:
    belge = belge_getir(db_conn, belge_kodu)
    if not belge:
        return {"basarili": False, "hata": "Belge bulunamadı"}
    
    eski_durum = belge['durum']
    gecerli_gecisler = {
        'taslak': ['incelemede'],
        'incelemede': ['aktif', 'taslak'],
        'aktif': ['arsiv'],
        'arsiv': []
    }
    
    if yeni_durum not in gecerli_gecisler.get(eski_durum, []):
        return {"basarili": False, "hata": f"Geçersiz durum geçişi: {eski_durum} -> {yeni_durum}"}
    
    sql = text("UPDATE qdms_belgeler SET durum = :durum, guncelleme_tarihi = CURRENT_TIMESTAMP WHERE belge_kodu = :kod")
    try:
        _exec_commit(db_conn, sql, {"durum": yeni_durum, "kod": belge_kodu})
        return {"basarili": True}
    except Exception as e:
        return {"basarili": False, "hata": str(e)}

def belge_getir(db_conn, belge_kodu: str) -> dict | None:
    sql = text("SELECT * FROM qdms_belgeler WHERE belge_kodu = :kod")
    try:
        if hasattr(db_conn, 'execute'):
            res = db_conn.execute(sql, {"kod": belge_kodu}).fetchone()
        else:
            with db_conn.connect() as conn:
                res = conn.execute(sql, {"kod": belge_kodu}).fetchone()
        if res: return dict(res._mapping)
    except: pass
    return None

def belge_listele(db_conn, filtre: dict = None) -> list:
    query = "SELECT * FROM qdms_belgeler WHERE 1=1"
    params = {}
    if filtre:
        if filtre.get('durum'):
            query += " AND durum = :durum"
            params['durum'] = filtre['durum']
    
    if hasattr(db_conn, 'connect'):
        with db_conn.connect() as conn:
            res = conn.execute(text(query), params).fetchall()
    else:
        res = db_conn.execute(text(query), params).fetchall()
    return [dict(r._mapping) for r in res]
