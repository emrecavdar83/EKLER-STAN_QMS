"""map_hesap.py — MAP Modülü Hesap Motoru
Pure fonksiyonlar — side-effect yok, test edilebilir.
pd.read_sql KULLANILMAZ — SQLAlchemy 2.x native execute + pd.DataFrame.
"""
import pandas as pd
from sqlalchemy import text


def _read(conn, sql: str, params: dict = None) -> pd.DataFrame:
    """pd.read_sql KULLANILMAZ. SQLAlchemy 2.x tam uyumlu native okuma."""
    result = conn.execute(text(sql), params or {})
    rows = result.fetchall()
    cols = list(result.keys())
    return pd.DataFrame(rows, columns=cols)


def hesapla_sure_ozeti(engine, vardiya_id: int) -> dict:
    with engine.connect() as conn:
        df = _read(conn, "SELECT * FROM map_zaman_cizelgesi WHERE vardiya_id=:v",
                   {"v": vardiya_id})
        vdf = _read(conn, "SELECT * FROM map_vardiya WHERE id=:v", {"v": vardiya_id})

    if vdf.empty:
        return {}

    calisma_dk = float(df[df['durum'] == 'CALISIYOR']['sure_dk'].fillna(0).sum())
    durus_dk = float(df[df['durum'] == 'DURUS']['sure_dk'].fillna(0).sum())
    mola_dk = float(
        df[df['neden'].astype(str).str.contains('Mola', na=False)]['sure_dk'].fillna(0).sum()
    )
    toplam_dk = calisma_dk + durus_dk
    kul_pct = round(calisma_dk / toplam_dk * 100, 1) if toplam_dk > 0 else 0
    net_toplam = toplam_dk - mola_dk
    net_kul_pct = round(calisma_dk / net_toplam * 100, 1) if net_toplam > 0 else 0

    return {
        "toplam_vardiya_dk": round(toplam_dk, 1),
        "toplam_calisma_dk": round(calisma_dk, 1),
        "toplam_durus_dk": round(durus_dk, 1),
        "mola_dk": round(mola_dk, 1),
        "net_durus_dk": round(durus_dk - mola_dk, 1),
        "kullanilabilirlik_pct": kul_pct,
        "net_kullanilabilirlik_pct": net_kul_pct,
    }


def hesapla_uretim(engine, vardiya_id: int) -> dict:
    ozet = hesapla_sure_ozeti(engine, vardiya_id)
    if not ozet:
        return {}

    with engine.connect() as conn:
        vdf = _read(conn,
            "SELECT hedef_hiz_paket_dk, gerceklesen_uretim FROM map_vardiya WHERE id=:v",
            {"v": vardiya_id})
        fire_df = _read(conn,
            "SELECT COALESCE(SUM(miktar_adet), 0) AS toplam FROM map_fire_kaydi WHERE vardiya_id=:v",
            {"v": vardiya_id})

    if vdf.empty:
        return {}

    hedef_hiz = float(vdf.iloc[0]['hedef_hiz_paket_dk'] or 4.2)
    gercek_uretim = int(vdf.iloc[0]['gerceklesen_uretim'] or 0)
    calisma_dk = ozet.get("toplam_calisma_dk", 0)
    teorik = round(calisma_dk * hedef_hiz, 0)
    fire_adet = int(fire_df.iloc[0]['toplam'] or 0)
    gercek_hiz = round(gercek_uretim / calisma_dk, 2) if calisma_dk > 0 else 0
    fire_pct = round(fire_adet / teorik * 100, 1) if teorik > 0 else 0
    hiz_fark = round((gercek_hiz - hedef_hiz) / hedef_hiz * 100, 1) if hedef_hiz > 0 else 0

    return {
        "teorik_uretim": int(teorik),
        "gerceklesen_uretim": gercek_uretim,
        "fire_adet": fire_adet,
        "fire_pct": fire_pct,
        "hedef_hiz": hedef_hiz,
        "gercek_hiz": gercek_hiz,
        "hiz_farki_pct": hiz_fark,
    }


def hesapla_durus_ozeti(engine, vardiya_id: int) -> list:
    sql = """SELECT neden, COUNT(*) as olay_sayisi, SUM(sure_dk) as toplam_dk
             FROM map_zaman_cizelgesi
             WHERE vardiya_id=:v AND durum='DURUS'
             GROUP BY neden ORDER BY toplam_dk DESC NULLS LAST"""
    with engine.connect() as conn:
        df = _read(conn, sql, {"v": vardiya_id})
    return df.to_dict("records") if not df.empty else []


def hesapla_fire_ozeti(engine, vardiya_id: int) -> list:
    sql = """SELECT fire_tipi, SUM(miktar_adet) as miktar
             FROM map_fire_kaydi WHERE vardiya_id=:v
             GROUP BY fire_tipi ORDER BY miktar DESC"""
    with engine.connect() as conn:
        df = _read(conn, sql, {"v": vardiya_id})
    if df.empty:
        return []
    toplam = df['miktar'].sum()
    df['pct'] = (df['miktar'] / toplam * 100).round(1) if toplam > 0 else 0
    return df.to_dict("records")
