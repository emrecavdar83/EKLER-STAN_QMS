import hashlib
import secrets
from datetime import datetime, timedelta
from sqlalchemy import text

def kalici_oturum_olustur(engine, kullanici_id: int, cihaz_bilgisi: str = None, ip_adresi: str = None, son_modul: str = 'portal') -> str:
    """Yeni bir kalıcı oturum oluşturur, çerez için ham token döner."""
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    gecerlilik = datetime.now() + timedelta(days=7) # Emre Bey: 7 gün yeterli
    
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO sistem_oturum_izleri (token_hash, kullanici_id, cihaz_bilgisi, ip_adresi, gecerlilik_ts, son_modul)
            VALUES (:th, :kid, :cb, :ip, :gt, :sm)
        """), {"th": token_hash, "kid": kullanici_id, "cb": cihaz_bilgisi, "ip": ip_adresi, "gt": gecerlilik, "sm": son_modul})
    
    return raw_token

def kalici_oturum_dogrula(engine, raw_token: str, cihaz_bilgisi: str = None) -> dict | None:
    """Çerezdeki token'ı doğrular ve kullanıcı bilgilerini döner."""
    if not raw_token: return None
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    
    sql = text("""
        SELECT p.*, b.bolum_adi as bolum, s.son_modul 
        FROM sistem_oturum_izleri s
        JOIN ayarlar_kullanicilar p ON s.kullanici_id = p.id
        LEFT JOIN ayarlar_bolumler b ON p.departman_id = b.id
        WHERE s.token_hash = :th 
          AND s.gecerlilik_ts > NOW()
          AND (s.cihaz_bilgisi = :cb OR :cb IS NULL)
    """)
    
    with engine.connect() as conn:
        res = conn.execute(sql, {"th": token_hash, "cb": cihaz_bilgisi}).fetchone()
        if res:
            # Oturum başarılı, son erişim zamanını güncelle
            conn.execute(text("UPDATE sistem_oturum_izleri SET son_erisim_ts = NOW() WHERE token_hash = :th"), {"th": token_hash})
            # Row'u dict'e çevir (SQLAlchemy 2.x)
            cols = res._fields
            return dict(zip(cols, res))
    return None

def oturum_modul_guncelle(engine, raw_token: str, modul_key: str):
    """Kullanıcının aktif olduğu son modülü veritabanında günceller."""
    if not raw_token or not modul_key: return
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    try:
        with engine.begin() as conn:
            conn.execute(text("UPDATE sistem_oturum_izleri SET son_modul = :m, son_erisim_ts = NOW() WHERE token_hash = :th"), 
                         {"m": modul_key, "th": token_hash})
    except Exception:
        pass # Migration henüz yapılmamış olabilir

def kalici_oturum_sil(engine, raw_token: str):
    """Oturum izini veritabanından siler."""
    if not raw_token: return
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM sistem_oturum_izleri WHERE token_hash = :th"), {"th": token_hash})
