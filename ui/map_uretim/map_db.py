"""map_db.py — MAP Üretim Modülü CRUD Katmanı
Anayasa: Sıfır hardcode, parametreli INSERT/UPDATE, to_sql YASAK.
pd.read_sql KULLANILMAZ — SQLAlchemy 2.x native execute + pd.DataFrame.
"""
import pandas as pd
from sqlalchemy import text
from datetime import datetime
import pytz

_TZ = pytz.timezone("Europe/Istanbul")


# ─── Yardımcı ───────────────────────────────────────────────────────────────
def _now_ts() -> str:
    return datetime.now(_TZ).strftime("%Y-%m-%d %H:%M:%S")


def _sure_dk(baslangic: str, bitis: str):
    try:
        fmt = "%Y-%m-%d %H:%M:%S"
        delta = datetime.strptime(bitis, fmt) - datetime.strptime(baslangic, fmt)
        return round(delta.total_seconds() / 60, 2)
    except Exception:
        return None


def _read(conn, sql: str, params: dict = None) -> pd.DataFrame:
    """pd.read_sql KULLANILMAZ. SQLAlchemy 2.x tam uyumlu okuma yöntemi."""
    result = conn.execute(text(sql), params or {})
    rows = result.fetchall()
    cols = list(result.keys())
    return pd.DataFrame(rows, columns=cols)


# ─── Vardiya ─────────────────────────────────────────────────────────────────
def get_aktif_vardiya(engine) -> dict | None:
    """Bugün açık olan tek vardiyayı döndürür."""
    bugun = datetime.now(_TZ).strftime("%Y-%m-%d")
    sql = "SELECT * FROM map_vardiya WHERE durum='ACIK' AND tarih=:t ORDER BY id DESC LIMIT 1"
    with engine.connect() as conn:
        df = _read(conn, sql, {"t": bugun})
    return df.iloc[0].to_dict() if not df.empty else None


def aç_vardiya(engine, makina_no, vardiya_no, operator_adi,
               vardiya_sefi, besleme, kasalama, hedef_hiz) -> int:
    """Yeni vardiya açar, id döndürür. Aynı anda 2 açık vardiaya izin vermez."""
    if get_aktif_vardiya(engine):
        raise ValueError("Zaten açık bir vardiya var! Önce kapatın.")
    ts = _now_ts()
    bugun = ts[:10]
    params = dict(tarih=bugun, makina=makina_no, vno=int(vardiya_no),
                  bas=ts[11:16], op=operator_adi, sef=vardiya_sefi,
                  bes=int(besleme), kas=int(kasalama), hiz=float(hedef_hiz))
    is_pg = engine.dialect.name == 'postgresql'
    with engine.begin() as conn:
        if is_pg:
            res = conn.execute(text("""
                INSERT INTO map_vardiya
                  (tarih, makina_no, vardiya_no, baslangic_saati, operator_adi,
                   vardiya_sefi, besleme_kisi, kasalama_kisi, hedef_hiz_paket_dk, durum)
                VALUES (:tarih,:makina,:vno,:bas,:op,:sef,:bes,:kas,:hiz,'ACIK')
                RETURNING id
            """), params)
            row = res.fetchone()
            return int(row[0]) if row else -1
        else:
            res = conn.execute(text("""
                INSERT INTO map_vardiya
                  (tarih, makina_no, vardiya_no, baslangic_saati, operator_adi,
                   vardiya_sefi, besleme_kisi, kasalama_kisi, hedef_hiz_paket_dk, durum)
                VALUES (:tarih,:makina,:vno,:bas,:op,:sef,:bes,:kas,:hiz,'ACIK')
            """), params)
            return int(res.lastrowid)


def kapat_vardiya(engine, vardiya_id: int, uretim: int):
    """Vardiyayı kapatır, açık zaman kayıtlarını da kapatır."""
    ts = _now_ts()
    with engine.begin() as conn:
        acik_df = _read(conn,
            "SELECT id, baslangic_ts FROM map_zaman_cizelgesi WHERE vardiya_id=:v AND bitis_ts IS NULL",
            {"v": vardiya_id})
        for _, row in acik_df.iterrows():
            dk = _sure_dk(row['baslangic_ts'], ts)
            conn.execute(text(
                "UPDATE map_zaman_cizelgesi SET bitis_ts=:b, sure_dk=:s WHERE id=:id"),
                dict(b=ts, s=dk, id=int(row['id'])))
        conn.execute(text("""
            UPDATE map_vardiya SET durum='KAPALI', bitis_saati=:bas,
              gerceklesen_uretim=:ur, guncelleme_ts=:ts WHERE id=:id
        """), dict(bas=ts[11:16], ur=int(uretim), ts=ts, id=vardiya_id))


# ─── Zaman Çizelgesi ─────────────────────────────────────────────────────────
def get_son_zaman_kaydi(engine, vardiya_id: int) -> dict | None:
    sql = "SELECT * FROM map_zaman_cizelgesi WHERE vardiya_id=:v ORDER BY sira_no DESC LIMIT 1"
    with engine.connect() as conn:
        df = _read(conn, sql, {"v": vardiya_id})
    return df.iloc[0].to_dict() if not df.empty else None


def insert_zaman_kaydi(engine, vardiya_id: int, durum: str,
                       neden: str = None, aciklama: str = None):
    """Yeni çalışma/duruş kaydı açar, önceki açık kaydı kapatır."""
    ts = _now_ts()
    with engine.begin() as conn:
        acik = _read(conn,
            "SELECT id, baslangic_ts FROM map_zaman_cizelgesi WHERE vardiya_id=:v AND bitis_ts IS NULL",
            {"v": vardiya_id})
        for _, row in acik.iterrows():
            dk = _sure_dk(row['baslangic_ts'], ts)
            conn.execute(text(
                "UPDATE map_zaman_cizelgesi SET bitis_ts=:b, sure_dk=:s WHERE id=:id"),
                dict(b=ts, s=dk, id=int(row['id'])))
        sira_df = _read(conn,
            "SELECT COALESCE(MAX(sira_no),0)+1 AS n FROM map_zaman_cizelgesi WHERE vardiya_id=:v",
            {"v": vardiya_id})
        sira = int(sira_df.iloc[0]['n'])
        conn.execute(text("""
            INSERT INTO map_zaman_cizelgesi(vardiya_id,sira_no,baslangic_ts,durum,neden,aciklama)
            VALUES(:vid,:sno,:ts,:dur,:ned,:acl)
        """), dict(vid=vardiya_id, sno=sira, ts=ts, dur=durum, ned=neden, acl=aciklama))


def get_zaman_cizelgesi(engine, vardiya_id: int) -> pd.DataFrame:
    sql = """SELECT sira_no,baslangic_ts,bitis_ts,sure_dk,durum,neden,aciklama
             FROM map_zaman_cizelgesi WHERE vardiya_id=:v ORDER BY sira_no"""
    with engine.connect() as conn:
        return _read(conn, sql, {"v": vardiya_id})


def sil_son_zaman_kaydi(engine, vardiya_id: int):
    sql = """DELETE FROM map_zaman_cizelgesi WHERE id=(
               SELECT id FROM map_zaman_cizelgesi WHERE vardiya_id=:v ORDER BY sira_no DESC LIMIT 1)"""
    with engine.begin() as conn:
        conn.execute(text(sql), {"v": vardiya_id})


def manuel_zaman_ekle(engine, vardiya_id: int, bas: str, bit: str,
                      durum: str, neden: str, aciklama: str, tarih: str):
    """Manuel mod: saat stringleri (HH:MM) ile kayıt ekler."""
    bas_ts = f"{tarih} {bas}:00"
    bit_ts = f"{tarih} {bit}:00"
    dk = _sure_dk(bas_ts, bit_ts)
    with engine.begin() as conn:
        sira_df = _read(conn,
            "SELECT COALESCE(MAX(sira_no),0)+1 AS n FROM map_zaman_cizelgesi WHERE vardiya_id=:v",
            {"v": vardiya_id})
        sira = int(sira_df.iloc[0]['n'])
        conn.execute(text("""
            INSERT INTO map_zaman_cizelgesi(vardiya_id,sira_no,baslangic_ts,bitis_ts,sure_dk,durum,neden,aciklama)
            VALUES(:vid,:sno,:bas,:bit,:dk,:dur,:ned,:acl)
        """), dict(vid=vardiya_id, sno=sira, bas=bas_ts, bit=bit_ts, dk=dk,
                   dur=durum, ned=neden, acl=aciklama))


# ─── Bobin ───────────────────────────────────────────────────────────────────
def insert_bobin(engine, vardiya_id: int, lot: str, bitis_m,
                 aciklama: str, baslangic_m: float = 300):
    ts = _now_ts()
    kullanilan = round(baslangic_m - (bitis_m or 0), 2) if bitis_m is not None else None
    with engine.begin() as conn:
        sira_df = _read(conn,
            "SELECT COALESCE(MAX(sira_no),0)+1 AS n FROM map_bobin_kaydi WHERE vardiya_id=:v",
            {"v": vardiya_id})
        sira = int(sira_df.iloc[0]['n'])
        conn.execute(text("""
            INSERT INTO map_bobin_kaydi(vardiya_id,sira_no,degisim_ts,bobin_lot,
              baslangic_m,bitis_m,kullanilan_m,aciklama)
            VALUES(:vid,:sno,:ts,:lot,:bas,:bit,:kul,:acl)
        """), dict(vid=vardiya_id, sno=sira, ts=ts, lot=lot, bas=float(baslangic_m),
                   bit=bitis_m, kul=kullanilan, acl=aciklama))


def get_bobinler(engine, vardiya_id: int) -> pd.DataFrame:
    with engine.connect() as conn:
        return _read(conn,
            "SELECT * FROM map_bobin_kaydi WHERE vardiya_id=:v ORDER BY sira_no",
            {"v": vardiya_id})


# ─── Fire ────────────────────────────────────────────────────────────────────
def insert_fire(engine, vardiya_id: int, fire_tipi: str, miktar: int,
                bobin_ref: str = None, aciklama: str = None):
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO map_fire_kaydi(vardiya_id,fire_tipi,miktar_adet,bobin_ref,aciklama)
            VALUES(:vid,:tip,:mik,:bref,:acl)
        """), dict(vid=vardiya_id, tip=fire_tipi, mik=int(miktar), bref=bobin_ref, acl=aciklama))


def get_fire_kayitlari(engine, vardiya_id: int) -> pd.DataFrame:
    with engine.connect() as conn:
        return _read(conn,
            "SELECT * FROM map_fire_kaydi WHERE vardiya_id=:v ORDER BY id",
            {"v": vardiya_id})
