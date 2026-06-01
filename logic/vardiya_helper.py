"""
Vardiya Helper Modülü (v8.0.0)
Sistem genelinde TEK KAYNAK — vardiya tipleri, izin günleri bit-mask, format dönüşümü.

X4-a kararı: Ayrı modül, açık sorumluluk.
S10 kararı: Tüm UI dosyaları bu helper'ı kullanacak.

Anayasa Uyumu:
  - Sıfır hardcode (Madde 1) — vardiya_tipleri DB'den okunur
  - Türkçe snake_case (Madde 2)
  - Maks 30 satır/fonksiyon (Madde 3)
"""
import re
from typing import List
import streamlit as st
from sqlalchemy import text


# ─── Bit-Mask Sabitleri ──────────────────────────────────────────────────────
GUN_BITMASK = {
    'Pzt': 1, 'Sal': 2, 'Çar': 4, 'Per': 8,
    'Cum': 16, 'Cmt': 32, 'Paz': 64,
}

# Tam isim → kısaltma (rapor/UI tutarlılığı için)
GUN_TAM_KISA = {
    'Pazartesi': 'Pzt', 'Salı': 'Sal', 'Çarşamba': 'Çar', 'Perşembe': 'Per',
    'Cuma': 'Cum', 'Cumartesi': 'Cmt', 'Pazar': 'Paz',
}
GUN_KISA_TAM = {v: k for k, v in GUN_TAM_KISA.items()}

# weekday() (0=Pzt) → bit-mask değeri
WEEKDAY_BITMASK = {0: 1, 1: 2, 2: 4, 3: 8, 4: 16, 5: 32, 6: 64}

_SAAT_REGEX = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_VARDIYA_REGEX = re.compile(r"^([01]\d|2[0-3]):[0-5]\d-([01]\d|2[0-3]):[0-5]\d$")


# ─── Bit-Mask Encode/Decode ──────────────────────────────────────────────────
def izin_encode(gunler: List[str]) -> int:
    """['Pzt','Sal'] → 3. Bilinmeyen kısaltma yoksayılır."""
    return sum(GUN_BITMASK[g] for g in (gunler or []) if g in GUN_BITMASK)


def izin_decode(bitmask: int) -> List[str]:
    """3 → ['Pzt','Sal']. Sıralı döner."""
    bm = int(bitmask or 0)
    return [g for g, v in GUN_BITMASK.items() if bm & v]


def izin_str(bitmask: int) -> str:
    """3 → 'Pzt, Sal'. 0 → '-' (UI için kısa görünüm)."""
    parts = izin_decode(bitmask)
    return ", ".join(parts) if parts else "-"


def izin_str_tam(bitmask: int) -> str:
    """3 → 'Pazartesi, Salı'. Rapor için tam isim."""
    parts = [GUN_KISA_TAM[g] for g in izin_decode(bitmask)]
    return ", ".join(parts) if parts else "-"


def gun_izinli_mi(bitmask: int, weekday: int) -> bool:
    """weekday (0=Pzt..6=Paz) için bit kontrolü. is_personnel_off helper'ı için."""
    return bool(int(bitmask or 0) & WEEKDAY_BITMASK.get(weekday, 0))


# ─── Vardiya Format Doğrulama ────────────────────────────────────────────────
def saat_dogrula(saat: str) -> bool:
    """'07:00' ✓"""
    return bool(_SAAT_REGEX.match(str(saat or "").strip()))


def vardiya_dogrula(vardiya: str) -> bool:
    """'07:00-15:00' ✓"""
    return bool(_VARDIYA_REGEX.match(str(vardiya or "").strip()))


def vardiya_olustur(baslangic: str, bitis: str) -> str:
    """('07:00', '15:00') → '07:00-15:00'. Doğrulama dahil."""
    if not (saat_dogrula(baslangic) and saat_dogrula(bitis)):
        raise ValueError(f"Geçersiz saat: {baslangic} veya {bitis}")
    return f"{baslangic.strip()}-{bitis.strip()}"


# ─── DB-Driven Vardiya Tipleri (TEK KAYNAK) ──────────────────────────────────
@st.cache_data(ttl=60)
def get_aktif_vardiyalar() -> List[str]:
    """DB'den aktif vardiya tip_adi listesini döner. Tüm UI burada birleşir."""
    try:
        from database.connection import get_engine
        with get_engine().connect() as conn:
            rows = conn.execute(text(
                "SELECT tip_adi FROM vardiya_tipleri "
                "WHERE aktif = 1 ORDER BY sira_no, id"
            )).fetchall()
        return [r[0] for r in rows] or _fallback_vardiyalar()
    except Exception:
        return _fallback_vardiyalar()


def _fallback_vardiyalar() -> List[str]:
    """DB erişimi yoksa minimum çalışır liste (Anayasa Madde 9 fail-safe)."""
    return ["07:00-15:00", "15:00-23:00", "23:00-07:00"]


def vardiya_secim_kutusu(label="Vardiya", key=None, default=None,
                         help=None) -> str:
    """Streamlit selectbox wrapper — tek satır kullanım için sistem genelinde DRY."""
    options = get_aktif_vardiyalar()
    idx = options.index(default) if default in options else 0
    return st.selectbox(label, options=options, index=idx, key=key, help=help)


# ─── İzin Günleri Multi-Select Widget ────────────────────────────────────────
def izin_multiselect(label="📅 Haftalık İzin Günleri", key=None,
                     mevcut_bitmask: int = 0) -> int:
    """7 gün multi-select. Bit-mask integer döner."""
    secili = izin_decode(mevcut_bitmask)
    secim = st.multiselect(
        label,
        options=list(GUN_BITMASK.keys()),
        default=secili,
        key=key,
        help="Birden fazla gün seçilebilir. Pzt=1, Sal=2, Çar=4, Per=8, Cum=16, Cmt=32, Paz=64"
    )
    return izin_encode(secim)
