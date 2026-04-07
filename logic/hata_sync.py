"""
EKLERİSTAN QMS — Hata Sync Motoru (v5.9.0)
Supabase'deki hata_loglari tablosunu yerel logs/hata_loglari/ dizinine indirir.
Her gün için ayrı JSONL dosyası oluşturur, tekrar kayıt engellidir.
"""
import json
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from sqlalchemy import text

HATA_DIZIN = Path("logs/hata_loglari")
SON_SYNC_DOSYA = HATA_DIZIN / ".son_sync"
MAX_INDIR = 1000  # Tek seferde en fazla


def _dizin_hazirla():
    HATA_DIZIN.mkdir(parents=True, exist_ok=True)


def bulut_hatalari_indir(engine) -> tuple[int, str]:
    """Supabase'den hata loglarını çeker, güne göre JSONL dosyasına ekler.
    Returns: (yeni_kayit_sayisi, mesaj)
    """
    _dizin_hazirla()
    try:
        with engine.connect() as conn:
            df = pd.read_sql(
                text(f"SELECT * FROM hata_loglari ORDER BY zaman DESC LIMIT {MAX_INDIR}"),
                conn
            )

        if df.empty:
            _son_sync_kaydet("Kayıt yok")
            return 0, "Bulutta henüz kayıt yok."

        # Mevcut kayıtları topla (tekrar engeli)
        mevcut_kodlar: set[str] = set()
        for f in HATA_DIZIN.glob("*_hata.jsonl"):
            with open(f, "r", encoding="utf-8") as fp:
                for satir in fp:
                    try:
                        mevcut_kodlar.add(json.loads(satir)["hata_kodu"])
                    except Exception:
                        pass

        # Güne göre grupla ve yaz
        yeni = 0
        for _, row in df.iterrows():
            kod = str(row.get("hata_kodu", ""))
            if kod in mevcut_kodlar:
                continue
            zaman_str = str(row.get("zaman", ""))
            try:
                gun = pd.to_datetime(zaman_str).strftime("%Y-%m-%d")
            except Exception:
                gun = datetime.now().strftime("%Y-%m-%d")
            dosya = HATA_DIZIN / f"{gun}_hata.jsonl"
            with open(dosya, "a", encoding="utf-8") as fp:
                fp.write(json.dumps(dict(row), default=str, ensure_ascii=False) + "\n")
            mevcut_kodlar.add(kod)
            yeni += 1

        _son_sync_kaydet(f"{yeni} yeni, toplam {len(df)}")
        return yeni, f"✅ {yeni} yeni kayıt indirildi (toplam sorgulanan: {len(df)})"

    except Exception as e:
        _son_sync_kaydet(f"HATA: {e}")
        return 0, f"❌ Sync hatası: {e}"


def _son_sync_kaydet(not_str: str):
    _dizin_hazirla()
    with open(SON_SYNC_DOSYA, "w", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat()} | {not_str}")


def son_sync_bilgisi() -> dict:
    """Son sync zamanı ve notunu döner."""
    if not SON_SYNC_DOSYA.exists():
        return {"zaman": None, "not": "Henüz sync yapılmadı"}
    icerik = SON_SYNC_DOSYA.read_text(encoding="utf-8").strip()
    parcalar = icerik.split(" | ", 1)
    return {
        "zaman": parcalar[0] if parcalar else None,
        "not": parcalar[1] if len(parcalar) > 1 else ""
    }


def yerel_hatalari_oku(max_gun: int = 30) -> pd.DataFrame:
    """Son max_gun günlük JSONL dosyalarını birleştirerek DataFrame döner."""
    _dizin_hazirla()
    satirlar = []
    dosyalar = sorted(HATA_DIZIN.glob("*_hata.jsonl"), reverse=True)[:max_gun]
    for dosya in dosyalar:
        with open(dosya, "r", encoding="utf-8") as f:
            for satir in f:
                try:
                    satirlar.append(json.loads(satir.strip()))
                except Exception:
                    pass
    if not satirlar:
        return pd.DataFrame()
    df = pd.DataFrame(satirlar)
    if "zaman" in df.columns:
        df["zaman"] = pd.to_datetime(df["zaman"], errors="coerce")
    if "hata_kodu" in df.columns:
        df = df.drop_duplicates(subset=["hata_kodu"])
    return df.sort_values("zaman", ascending=False) if "zaman" in df.columns else df


def yerel_dosya_listesi() -> list[dict]:
    """logs/hata_loglari/ içindeki JSONL dosyalarını meta bilgisiyle listeler."""
    _dizin_hazirla()
    sonuc = []
    for d in sorted(HATA_DIZIN.glob("*_hata.jsonl"), reverse=True):
        try:
            kayit = sum(1 for _ in open(d, encoding="utf-8"))
            sonuc.append({
                "Dosya": d.name,
                "Kayıt Sayısı": kayit,
                "Boyut": f"{d.stat().st_size / 1024:.1f} KB",
                "Son Güncelleme": datetime.fromtimestamp(d.stat().st_mtime).strftime("%d.%m.%Y %H:%M"),
            })
        except Exception:
            pass
    return sonuc


def hata_istatistikleri(df: pd.DataFrame) -> dict:
    """DataFrame'den özet istatistik üretir."""
    if df.empty:
        return {}
    stats = {
        "toplam": len(df),
        "cozuldu": int(df["is_fixed"].sum()) if "is_fixed" in df.columns else 0,
        "kritik": len(df[df["seviye"] == "CRITICAL"]) if "seviye" in df.columns else 0,
        "modul_dagilimi": {},
        "gun_dagilimi": {},
        "seviye_dagilimi": {},
    }
    if "modul" in df.columns:
        stats["modul_dagilimi"] = df["modul"].value_counts().head(10).to_dict()
    if "zaman" in df.columns:
        gun_df = df.dropna(subset=["zaman"]).copy()
        gun_df["gun"] = gun_df["zaman"].dt.strftime("%Y-%m-%d")
        stats["gun_dagilimi"] = gun_df["gun"].value_counts().sort_index().to_dict()
    if "seviye" in df.columns:
        stats["seviye_dagilimi"] = df["seviye"].value_counts().to_dict()
    return stats
