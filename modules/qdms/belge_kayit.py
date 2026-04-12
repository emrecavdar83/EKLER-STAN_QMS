"""
EKLERİSTAN QDMS — Belge Kayıt Modülü
Belge CRUD, durum yönetimi, kod formatı doğrulama
"""
import re
from sqlalchemy import text

def belge_kodu_oner(db_conn, belge_tipi: str) -> str:
    """Seçilen tipe göre sıradaki boş belge kodunu önerir. Format: EKL-[TIP]-NNN"""
    query = text("SELECT belge_kodu FROM qdms_belgeler WHERE belge_tipi = :tip ORDER BY belge_kodu")
    try:
        if hasattr(db_conn, 'connect'):
            with db_conn.connect() as conn:
                rows = conn.execute(query, {"tip": belge_tipi}).fetchall()
        else:
            rows = db_conn.execute(query, {"tip": belge_tipi}).fetchall()
        max_no = 0
        prefix = f"EKL-{belge_tipi.upper()}-"
        for row in rows:
            kod = row[0]
            if kod.startswith(prefix):
                try:
                    no = int(kod[len(prefix):])
                    if no > max_no:
                        max_no = no
                except ValueError:
                    pass
        return f"{prefix}{max_no + 1:03d}"
    except Exception:
        return f"EKL-{belge_tipi.upper()}-001"


def belge_kod_dogrula(belge_kodu: str) -> bool:
    """Format: EKL-[TIP]-[2-4 HANE]
    Desteklenen Tipler: SO, TL, PR, KYS, UR, HACCP, FR, PL, GT, LS, KL, YD, SOP
    """
    pattern = r"^EKL-(SO|TL|PR|KYS|UR|HACCP|FR|PL|GT|LS|KL|YD|SOP|GK)-\d{2,4}$"
    return bool(re.match(pattern, str(belge_kodu).upper().strip()))

def _exec_commit(db_conn, sql, params):
    """SQLAlchemy 2.0 uyumlu güvenli execute + commit."""
    # 1. Engine gelirse (Yüksek seviye çağrı): connect() veya begin() ile transaction yönetir.
    # isinstance(db_conn, Engine) dairesel import nedeniyle hasattr ile kontrol edilir.
    if hasattr(db_conn, 'connect') and not hasattr(db_conn, 'commit'): 
        with db_conn.connect() as conn:
            with conn.begin():
                return conn.execute(sql, params)
    
    # 2. Connection veya Session gelirse (Düşük seviye çağrı):
    return db_conn.execute(sql, params)

def belge_olustur(db_conn, belge_kodu: str, belge_adi: str, belge_tipi: str, alt_kategori: str, aciklama: str, olusturan_id: int, **kwargs) -> dict:
    """Yeni bir döküman kaydı oluşturur (v3.4: BRC/IFS Uyumlu)"""
    sql = text("""
        INSERT INTO qdms_belgeler (belge_kodu, belge_adi, belge_tipi, alt_kategori, aciklama, olusturan_id, amac, kapsam, tanimlar, dokumanlar, icerik)
        VALUES (:kod, :ad, :tip, :kat, :aciklama, :oid, :amac, :kapsam, :tanimlar, :dokumanlar, :icerik)
    """)
    try:
        params = {
            "kod": belge_kodu, "ad": belge_adi, "tip": belge_tipi, "kat": alt_kategori,
            "aciklama": aciklama, "oid": olusturan_id,
            "amac": kwargs.get('amac', ''), "kapsam": kwargs.get('kapsam', ''),
            "tanimlar": kwargs.get('tanimlar', ''), "dokumanlar": kwargs.get('dokumanlar', ''),
            "icerik": kwargs.get('icerik', '')
        }
        _exec_commit(db_conn, sql, params)
        # ISO 9001: Belge oluşturma denetim kaydı
        try:
            _exec_commit(db_conn, text(
                "INSERT INTO sistem_loglari (islem_tipi, detay, modul) VALUES (:i, :d, :m)"
            ), {"i": "QDMS_BELGE_OLUSTUR", "d": f"Belge oluşturuldu: {belge_kodu} ({belge_tipi}) - Kullanıcı ID: {olusturan_id}", "m": "qdms"})
        except Exception: pass
        return {"basarili": True, "belge_kodu": belge_kodu}
    except Exception as e:
        return {"basarili": False, "hata": str(e)}

def belge_guncelle(db_conn, belge_kodu: str, belge_adi: str, alt_kategori: str, aciklama: str, **kwargs) -> dict:
    """Belge temel bilgilerini ve BRC/IFS alanlarını günceller (v3.4)."""
    sql = text("""
        UPDATE qdms_belgeler 
        SET belge_adi = :ad, alt_kategori = :kat, aciklama = :aciklama,
            amac = :amac, kapsam = :kapsam, tanimlar = :tanimlar, dokumanlar = :dokumanlar, icerik = :icerik,
            guncelleme_tarihi = CURRENT_TIMESTAMP
        WHERE belge_kodu = :kod
    """)
    try:
        params = {
            "ad": belge_adi, "kat": alt_kategori, "aciklama": aciklama, "kod": belge_kodu,
            "amac": kwargs.get('amac', ''), "kapsam": kwargs.get('kapsam', ''),
            "tanimlar": kwargs.get('tanimlar', ''), "dokumanlar": kwargs.get('dokumanlar', ''),
            "icerik": kwargs.get('icerik', '')
        }
        _exec_commit(db_conn, sql, params)
        # ISO 9001: Belge güncelleme denetim kaydı
        try:
            _exec_commit(db_conn, text(
                "INSERT INTO sistem_loglari (islem_tipi, detay, modul) VALUES (:i, :d, :m)"
            ), {"i": "QDMS_BELGE_GUNCELLE", "d": f"Belge güncellendi: {belge_kodu}", "m": "qdms"})
        except Exception: pass
        return {"basarili": True}
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
        # ISO 9001: Belge durum geçişi denetim kaydı (BRC/IFS uyumluluk)
        try:
            _exec_commit(db_conn, text(
                "INSERT INTO sistem_loglari (islem_tipi, detay, modul) VALUES (:i, :d, :m)"
            ), {"i": "QDMS_DURUM_GECIS", "d": f"{belge_kodu}: {eski_durum} → {yeni_durum} | Güncelleyen ID: {guncelleyen_id}", "m": "qdms"})
        except Exception: pass
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
    except Exception as _e:
        print(f"BELGE_GETIR_ERR [{belge_kodu}]: {_e}")
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
